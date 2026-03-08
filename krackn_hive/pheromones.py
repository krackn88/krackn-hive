from .models import HiveSignal


class PheromoneScorer:
    def signal_score(self, signal: HiveSignal) -> float:
        freshness = max(0.2, signal.confidence)
        return signal.score * freshness
