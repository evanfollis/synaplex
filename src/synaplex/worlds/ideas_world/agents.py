# synaplex/worlds/ideas_world/agents.py

from pathlib import Path
from typing import Any, Dict, List, Optional

from synaplex.core.ids import AgentId
from synaplex.core.messages import MessageId, Signal
from synaplex.cognition.openai_client import OpenAILLMClient
from synaplex.cognition.mind import Mind
from synaplex.cognition.manifolds import FileManifoldStore
from synaplex.core.world_modes import WorldMode


class IdeasArchivistMind(Mind):
    """
    Archivist mind that reads markdown idea files and emits idea signals.
    
    This agent processes idea markdown files and creates structured signals
    that other agents can consume.
    """
    
    def __init__(
        self,
        agent_id: AgentId,
        ideas_dir: Path,
        llm_client: Optional[OpenAILLMClient] = None,
        **kwargs
    ):
        super().__init__(
            agent_id=agent_id,
            llm_client=llm_client or OpenAILLMClient(),
            world_mode=WorldMode.REASONING_ONLY,  # Archivist doesn't need manifold, just processes files
            **kwargs
        )
        self.ideas_dir = Path(ideas_dir)
        self._processed_files: Dict[str, float] = {}  # file -> mtime
    
    def get_visible_state(self) -> Dict[str, Any]:
        """Expose current idea processing state."""
        return {
            "ideas_dir": str(self.ideas_dir),
            "processed_files": list(self._processed_files.keys()),
        }
    
    def _extract_ideas_from_markdown(self, content: str, filepath: str) -> List[Dict[str, Any]]:
        """
        Extract idea atoms from markdown content.
        
        Looks for sections like:
        ## Idea: Title
        - Domain: ...
        - Tags: ...
        - Status: ...
        - Question: ...
        """
        ideas = []
        lines = content.split('\n')
        current_idea = None
        current_content = []
        
        for line in lines:
            if line.startswith('## Idea:'):
                # Save previous idea if exists
                if current_idea is not None:
                    current_idea['content'] = '\n'.join(current_content).strip()
                    ideas.append(current_idea)
                
                # Start new idea
                title = line.replace('## Idea:', '').strip()
                current_idea = {
                    'title': title,
                    'source_file': filepath,
                    'domain': None,
                    'tags': [],
                    'status': None,
                    'question': None,
                }
                current_content = []
            
            elif current_idea is not None:
                # Parse metadata lines
                if line.startswith('- Domain:'):
                    current_idea['domain'] = line.replace('- Domain:', '').strip()
                elif line.startswith('- Tags:'):
                    tags_str = line.replace('- Tags:', '').strip()
                    # Parse tags from [tag1, tag2] or comma-separated
                    tags_str = tags_str.strip('[]')
                    current_idea['tags'] = [t.strip() for t in tags_str.split(',') if t.strip()]
                elif line.startswith('- Status:'):
                    current_idea['status'] = line.replace('- Status:', '').strip()
                elif line.startswith('- Question:'):
                    current_idea['question'] = line.replace('- Question:', '').strip()
                elif line.startswith('##'):  # New section, end current idea
                    if current_idea:
                        current_idea['content'] = '\n'.join(current_content).strip()
                        ideas.append(current_idea)
                        current_idea = None
                        current_content = []
                else:
                    current_content.append(line)
        
        # Don't forget last idea
        if current_idea is not None:
            current_idea['content'] = '\n'.join(current_content).strip()
            ideas.append(current_idea)
        
        return ideas
    
    def act(self, reasoning_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process markdown files and emit idea signals.
        
        This scans the ideas directory for markdown files, extracts ideas,
        and emits signals for other agents to consume.
        """
        signals = []
        
        # Scan markdown files in ideas directory
        if not self.ideas_dir.exists():
            return {"signals": [], "requests": [], "env_updates": {}}
        
        markdown_files = list(self.ideas_dir.glob("*.md"))
        
        for md_file in markdown_files:
            # Check if file has been modified
            mtime = md_file.stat().st_mtime
            if md_file.name in self._processed_files:
                if mtime <= self._processed_files[md_file.name]:
                    continue  # Already processed
            
            # Read and extract ideas
            try:
                content = md_file.read_text(encoding='utf-8')
                ideas = self._extract_ideas_from_markdown(content, md_file.name)
                
                for idea in ideas:
                    # Emit signal for each idea
                    signal = {
                        "payload": {
                            "type": "idea",
                            "title": idea['title'],
                            "domain": idea.get('domain'),
                            "tags": idea.get('tags', []),
                            "status": idea.get('status', 'seed'),
                            "question": idea.get('question'),
                            "content_preview": idea.get('content', '')[:200],
                            "source_file": idea['source_file'],
                        }
                    }
                    signals.append(signal)
                
                self._processed_files[md_file.name] = mtime
                
            except Exception as e:
                # Skip problematic files, but log
                continue
        
        return {
            "signals": signals,
            "requests": [],
            "env_updates": {},
        }


def make_archivist_mind(
    agent_id: str = "archivist",
    ideas_dir: str | Path = "docs/ideas",
    **kwargs
) -> IdeasArchivistMind:
    """Factory for archivist mind."""
    return IdeasArchivistMind(
        agent_id=AgentId(agent_id),
        ideas_dir=Path(ideas_dir),
        **kwargs
    )


def make_architect_mind(
    agent_id: str = "architect",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for architect mind."""
    llm = OpenAILLMClient()
    store = FileManifoldStore(root=store_root or "manifolds/ideas_world") if store_root else None
    
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        manifold_store=store,
        world_mode=WorldMode.MANIFOLD,
        **kwargs
    )


def make_critic_mind(
    agent_id: str = "critic",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for critic mind."""
    llm = OpenAILLMClient()
    store = FileManifoldStore(root=store_root or "manifolds/ideas_world") if store_root else None
    
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        manifold_store=store,
        world_mode=WorldMode.MANIFOLD,
        **kwargs
    )


def make_synaplex_mind(
    agent_id: str = "synaplex",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for Synaplex idea mind."""
    llm = OpenAILLMClient()
    store = FileManifoldStore(root=store_root or "manifolds/ideas_world") if store_root else None
    
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        manifold_store=store,
        world_mode=WorldMode.MANIFOLD,
        **kwargs
    )


def make_topic_mind(
    agent_id: str,
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for topic expert minds."""
    llm = OpenAILLMClient()
    store = FileManifoldStore(root=store_root or "manifolds/ideas_world") if store_root else None
    
    return Mind(
        agent_id=AgentId(agent_id),
        llm_client=llm,
        manifold_store=store,
        world_mode=WorldMode.MANIFOLD,
        **kwargs
    )


# Convenience factories for each topic agent
def make_llms_mind(
    agent_id: str = "llms",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for LLMs topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_world_models_mind(
    agent_id: str = "world_models",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for World Models topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_agentic_systems_mind(
    agent_id: str = "agentic_systems",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for Agentic Systems topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_cognitive_architectures_mind(
    agent_id: str = "cognitive_architectures",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for Cognitive Architectures topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_manifolds_mind(
    agent_id: str = "manifolds",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for Manifolds topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_message_graphs_mind(
    agent_id: str = "message_graphs",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for Message Graphs topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)


def make_nature_nurture_mind(
    agent_id: str = "nature_nurture",
    store_root: Optional[str] = None,
    **kwargs
) -> Mind:
    """Factory for Nature vs Nurture topic mind."""
    return make_topic_mind(agent_id=agent_id, store_root=store_root, **kwargs)

