type FollowUpQuestionsProps = {
  questions: string[];
  onSelect: (question: string) => void;
};

export function FollowUpQuestions({
  questions,
  onSelect,
}: FollowUpQuestionsProps) {
  if (!questions || questions.length === 0) return null;

  console.log(questions);

  return (
    <div className="mt-3 flex flex-wrap gap-2">
      {questions.map((q) => (
        <button
          key={q}
          type="button"
          onClick={() => onSelect(q)}
          className="rounded-full border border-stone-200 bg-white px-3 py-1.5 text-sm text-stone-600 transition-colors hover:border-stone-300 hover:bg-stone-100 hover:text-neutral-900"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
