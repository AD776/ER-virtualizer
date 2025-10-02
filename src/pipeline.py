"""Core pipeline responsible for turning text into Wikidata triplets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence


EntityRecord = Mapping[str, str]
RelationshipRecord = Mapping[str, object]


@dataclass
class Pipeline:
    """Coordinate entity extraction with knowledge graph lookups."""

    entity_extractor: object
    kg_client: object

    def generate_triplets(self, text: str) -> List[MutableMapping[str, str]]:
        """Return S–P–O triplets discovered for *text*."""

        if not isinstance(text, str):  # defensive: the contract expects text input
            raise TypeError("text must be a str")

        raw_entities = list(self._extract_entities(text))
        if not raw_entities:
            return []

        entities = self._enrich_entities(raw_entities)
        if not entities:
            return []

        triplets: List[MutableMapping[str, str]] = []

        for subject in entities:
            subject_qid = subject.get("qid")
            if not subject_qid:
                continue

            for obj in entities:
                if subject is obj:
                    continue

                object_qid = obj.get("qid")
                if not object_qid or object_qid == subject_qid:
                    continue

                relationship = self._pick_relationship(subject_qid, object_qid)
                if relationship is None:
                    continue

                triplets.append(
                    {
                        "subject": subject.get("label", subject.get("mention", "")),
                        "subject_qid": subject_qid,
                        "subject_type": subject.get("type", ""),
                        "predicate": relationship["label"],
                        "predicate_pid": relationship["pid"],
                        "object": obj.get("label", obj.get("mention", "")),
                        "object_qid": object_qid,
                        "object_type": obj.get("type", ""),
                    }
                )

        return triplets

    def _extract_entities(self, text: str) -> Sequence[EntityRecord]:
        if not hasattr(self.entity_extractor, "extract"):
            raise AttributeError("entity_extractor must provide an 'extract' method")
        entities = self.entity_extractor.extract(text)
        if entities is None:
            return []
        return entities

    def _enrich_entities(self, entities: Sequence[EntityRecord]) -> List[Dict[str, str]]:
        enriched: Dict[str, Dict[str, str]] = {}

        for entity in entities:
            data = dict(entity)

            if not data.get("qid"):
                resolved = self._resolve_entity(data.get("mention") or data.get("label"))
                if resolved:
                    data.setdefault("label", resolved.get("label", ""))
                    if resolved.get("qid"):
                        data["qid"] = resolved["qid"]

            qid = data.get("qid")
            if not qid:
                key = data.get("mention") or data.get("label") or ""
            else:
                key = qid

            if key not in enriched:
                enriched[key] = data
            else:
                existing = enriched[key]
                if not existing.get("label") and data.get("label"):
                    existing["label"] = data["label"]
                if not existing.get("qid") and data.get("qid"):
                    existing["qid"] = data["qid"]
                if not existing.get("type") and data.get("type"):
                    existing["type"] = data["type"]

        return list(enriched.values())

    def _resolve_entity(self, text: Optional[str]) -> Optional[Mapping[str, str]]:
        if not text or not hasattr(self.kg_client, "resolve_entity"):
            return None
        resolved = self.kg_client.resolve_entity(text)
        if not resolved:
            return None
        return resolved

    def _pick_relationship(self, subject_qid: str, object_qid: str) -> Optional[Mapping[str, str]]:
        if not hasattr(self.kg_client, "get_relationships"):
            raise AttributeError("kg_client must provide a 'get_relationships' method")

        relationships: Iterable[RelationshipRecord] = self.kg_client.get_relationships(
            subject_qid, object_qid
        )
        best_label: Optional[str] = None
        best_pid: Optional[str] = None

        for relationship in relationships or []:
            pid = relationship.get("pid")
            labels = relationship.get("labels")
            if pid is None or not labels:
                continue

            candidate = self._select_shortest_label(labels)
            if candidate is None:
                continue

            if best_label is None or len(candidate) < len(best_label):
                best_label = candidate
                best_pid = str(pid)

        if best_label is None or best_pid is None:
            return None

        return {"label": best_label, "pid": best_pid}

    @staticmethod
    def _select_shortest_label(labels: Iterable[str]) -> Optional[str]:
        shortest: Optional[str] = None
        for label in labels:
            if not isinstance(label, str):
                continue
            label = label.strip()
            if not label:
                continue
            if shortest is None or len(label) < len(shortest):
                shortest = label
        return shortest
