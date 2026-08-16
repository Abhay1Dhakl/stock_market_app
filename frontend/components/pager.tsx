type PagerProps = {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  label: string;
};

export function Pager({ page, totalPages, onPageChange, label }: PagerProps) {
  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav aria-label={label} className="pager">
      <button
        className="pager__button"
        disabled={page === 1}
        onClick={() => onPageChange(page - 1)}
        type="button"
      >
        Prev
      </button>
      {Array.from({ length: totalPages }, (_, index) => index + 1).map((pageNumber) => (
        <button
          key={pageNumber}
          aria-current={pageNumber === page ? "page" : undefined}
          className={`pager__button${pageNumber === page ? " pager__button--active" : ""}`}
          onClick={() => onPageChange(pageNumber)}
          type="button"
        >
          {pageNumber}
        </button>
      ))}
      <button
        className="pager__button"
        disabled={page === totalPages}
        onClick={() => onPageChange(page + 1)}
        type="button"
      >
        Next
      </button>
    </nav>
  );
}
