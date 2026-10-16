"""Fixed-size browser cards avoid relayout and identical-content refreshes."""
from textual.widgets import Static


class FixedStatic(Static):
    def update(self, content="", *, layout=True):
        if content == getattr(self, '_web_content', None):
            return
        self._web_content = content
        super().update(content, layout=False)
