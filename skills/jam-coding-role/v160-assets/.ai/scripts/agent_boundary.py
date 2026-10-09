"""Pure identity rules. Stage authority is checked by workflow_state."""
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Actor:
    session: str
    root_session: str
    is_root: bool
    parent_session: str | None = None


def can_spawn(actor: Actor, *, role_can_spawn: bool = False,
              delegate_depth_left: int = 0, stage_bound: bool = False) -> bool:
    if stage_bound:
        return bool(actor.session and actor.root_session and role_can_spawn
                    and delegate_depth_left > 0)
    return bool(actor.session and actor.is_root and actor.session == actor.root_session)


def can_contact(actor_id: str, target_id: str, actors: Mapping[str, Actor],
                *, readonly_technical_p2p: bool = True) -> bool:
    actor, target = actors.get(actor_id), actors.get(target_id)
    if not actor or not target or actor_id == target_id:
        return False
    if not actor.root_session or actor.root_session != target.root_session:
        return False
    if readonly_technical_p2p:
        return True
    return target.parent_session == actor.session
