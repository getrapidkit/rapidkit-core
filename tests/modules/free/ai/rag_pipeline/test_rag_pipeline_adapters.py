def test_rag_pipeline_accepts_custom_generator(rendered_rag_pipeline) -> None:  # type: ignore[no-untyped-def]
    vendor = rendered_rag_pipeline["vendor"]

    def generator(prompt: str, context: dict[str, object]) -> str:
        return f"custom:{len(context['citations'])}:{prompt.splitlines()[0]}"

    pipeline = vendor.RagPipeline(generator=generator)
    pipeline.ingest(id="doc", text="Custom generators can call an LLM gateway.")

    answer = pipeline.answer("What can generators call?")

    assert answer.answer.startswith("custom:1:Answer using only")
