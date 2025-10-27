interface ErrorMessageProps {
  message?: string;
  id?: string;
}

export const ErrorMessage = ({ message, id }: ErrorMessageProps) => (
  <>
    {message && (
      <div className="h-7 flex items-start">
        {message && (
          <div id={id} className="text-red-500 text-xl font-semibold">
            {message}
          </div>
        )}
      </div>
    )}
  </>
);

