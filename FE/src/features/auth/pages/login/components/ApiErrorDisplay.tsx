interface ApiErrorDisplayProps {
  error: string | null;
}

export const ApiErrorDisplay = ({ error }: ApiErrorDisplayProps) =>
  error ? (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
      <div className="text-red-700 font-medium text-xl">{error}</div>
    </div>
  ) : null;

