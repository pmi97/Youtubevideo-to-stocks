import { InputHTMLAttributes, forwardRef } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    hint?: string;
    icon?: string;
    error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ label, hint, icon, error, className = '', ...props }, ref) => {
        return (
            <div className="space-y-2">
                {label && (
                    <label className="flex items-center gap-2 text-sm font-medium text-white/90">
                        {icon && <span>{icon}</span>}
                        {label}
                    </label>
                )}
                <input
                    ref={ref}
                    className={`input-base ${error ? 'border-red-500 ring-red-500/30' : ''} ${className}`}
                    {...props}
                />
                {hint && !error && (
                    <span className="text-xs text-gray-500">{hint}</span>
                )}
                {error && (
                    <span className="text-xs text-red-400">{error}</span>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';
