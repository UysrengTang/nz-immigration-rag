from app.db.repositories.base import BaseRepository
from app.schemas.ops import EvaluationResultRecord, EvaluationRunRecord


class EvaluationsRepository(BaseRepository):
    def create_evaluation_run(self, run: EvaluationRunRecord) -> EvaluationRunRecord:
        query = """
            insert into evaluation_runs (
                dataset_name,
                status,
                metrics,
                started_at,
                completed_at
            )
            values (%s, %s, %s, coalesce(%s, now()), %s)
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    run.dataset_name,
                    run.status.value,
                    self._jsonb(run.metrics),
                    run.started_at,
                    run.completed_at,
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Evaluation run insert returned no row.")
        return EvaluationRunRecord.model_validate(row)

    def add_evaluation_result(
        self,
        result: EvaluationResultRecord,
    ) -> EvaluationResultRecord:
        query = """
            insert into evaluation_results (
                evaluation_run_id,
                example_id,
                query,
                expected_outcome,
                actual_answer,
                actual_grounded,
                actual_refusal,
                citation_coverage_score,
                groundedness_score,
                evaluator_notes,
                metadata
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            returning *
        """
        with self._connection_factory() as conn, conn.cursor() as cur:
            cur.execute(
                query,
                (
                    str(result.evaluation_run_id),
                    result.example_id,
                    result.query,
                    result.expected_outcome,
                    result.actual_answer,
                    result.actual_grounded,
                    result.actual_refusal,
                    result.citation_coverage_score,
                    result.groundedness_score,
                    result.evaluator_notes,
                    self._jsonb(result.metadata),
                ),
            )
            row = cur.fetchone()

        if row is None:
            raise RuntimeError("Evaluation result insert returned no row.")
        return EvaluationResultRecord.model_validate(row)
