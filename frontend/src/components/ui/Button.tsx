import { ButtonHTMLAttributes, forwardRef } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary';
    loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ children, variant = 'primary', loading, disabled, className = '', ...props }, ref) => {
        const baseStyles = variant === 'primary'
            ? 'btn-primary'
            : 'btn-secondary';

        return (
            <button
                ref={ref}
                disabled={disabled || loading}
                className={`${baseStyles} inline-flex items-center justify-center gap-2 ${className}`}
                {...props}
            >
                {loading ? (
                    <>
                        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
                        <span>Processing...</span>
                    </>
                ) : (
                    children
                )}
            </button>
        );
    }
);

Button.displayName = 'Button';
