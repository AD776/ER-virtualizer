"""Wikidata client utilities for entity and relationship lookups."""

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Mapping, Optional, Sequence

try:
    import requests
except Exception:  # pragma: no cover - requests import is optional during tests
    requests = None


_LOGGER = logging.getLogger(__name__)


class WikidataClient:
    """Minimal client for Wikidata entity resolution and relationship discovery."""

    api_url = "https://www.wikidata.org/w/api.php"
    entity_data_url = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

    def __init__(
        self,
        language: str = "en",
        session: Optional["requests.Session"] = None,
        timeout: int = 10,
        user_agent: str = "EntityRelationshipVisualizer/1.0 (mailto:student@example.com)"
    ):
        if requests is None:
            raise ImportError("The 'requests' package is required for WikidataClient.")
        self.language = language
        self.timeout = timeout
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = user_agent
        self._property_label_cache: Dict[str, List[str]] = {}
        self._entity_cache: Dict[str, Mapping[str, object]] = {}

    # ---------------------------------------------------------------------
    # Entity resolution
    # ---------------------------------------------------------------------
    def resolve_entity(self, text: str) -> Optional[Mapping[str, str]]:
        if not text:
            return None

        params = {
            "action": "wbsearchentities",
            "search": text,
            "language": self.language,
            "format": "json",
            "limit": 1,
        }

        try:
            response = self.session.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network issues
            _LOGGER.debug("Failed to resolve entity '%s': %s", text, exc)
            return None

        payload = response.json()
        hits = payload.get("search", [])
        if not hits:
            return None

        top = hits[0]
        return {
            "qid": top.get("id", ""),
            "label": top.get("label", text),
        }

    # ---------------------------------------------------------------------
    # Relationship discovery
    # ---------------------------------------------------------------------
    def get_relationships(self, subject_qid: str, object_qid: str) -> List[Mapping[str, Sequence[str]]]:
        if not subject_qid or not object_qid:
            return []

        entity = self._get_entity(subject_qid)
        if not entity:
            return []

        claims = entity.get("claims", {})
        results: List[Mapping[str, Sequence[str]]] = []

        for pid, statements in claims.items():
            if not isinstance(statements, list):
                continue

            for statement in statements:
                mainsnak = statement.get("mainsnak", {})
                if mainsnak.get("snaktype") != "value":
                    continue

                datavalue = mainsnak.get("datavalue", {})
                if datavalue.get("type") != "wikibase-entityid":
                    continue

                value = datavalue.get("value", {})
                numeric_id = value.get("numeric-id")
                if numeric_id is None:
                    continue

                target_qid = f"Q{numeric_id}"
                if target_qid != object_qid:
                    continue

                labels = self._get_property_labels(pid)
                if not labels:
                    labels = [pid]

                results.append({"pid": pid, "labels": labels})

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_entity(self, qid: str) -> Optional[Mapping[str, object]]:
        if not qid:
            return None
        if qid in self._entity_cache:
            return self._entity_cache[qid]

        url = self.entity_data_url.format(qid)
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network issues
            _LOGGER.debug("Failed to fetch entity data for %s: %s", qid, exc)
            return None

        data = response.json()
        entity = (data.get("entities", {}) or {}).get(qid)
        if entity:
            self._entity_cache[qid] = entity
        return entity

    def _get_property_labels(self, pid: str) -> List[str]:
        if not pid:
            return []
        if pid in self._property_label_cache:
            return self._property_label_cache[pid]

        params = {
            "action": "wbgetentities",
            "ids": pid,
            "format": "json",
            "props": "labels",
            "languages": self.language,
        }

        try:
            response = self.session.get(self.api_url, params=params, timeout=self.timeout)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - network issues
            _LOGGER.debug("Failed to fetch labels for %s: %s", pid, exc)
            return []

        payload = response.json()
        entities = payload.get("entities", {})
        entity = entities.get(pid, {})
        labels = entity.get("labels", {})

        collected: List[str] = []
        for label in labels.values():
            value = label.get("value")
            if isinstance(value, str) and value:
                collected.append(value)

        self._property_label_cache[pid] = collected
        return collected
