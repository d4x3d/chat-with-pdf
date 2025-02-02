'use client';

import { InputHTMLAttributes, forwardRef } from 'react';
import { twMerge } from 'tailwind-merge';

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, label, type = 'text', ...props }, ref) => {
    // Base styles for the input
    const baseStyles = `
      w-full
      px-4
      py-2
      transition-all
      duration-200
      bg-white
      border-2
      rounded-xl
      outline-none
      dark:bg-gray-900
      focus:ring-2
      focus:ring-blue-500/20
      dark:focus:ring-blue-500/40
      ${error ? 'border-red-500' : 'border-gray-200 dark:border-gray-700'}
      ${error ? 'focus:border-red-500' : 'focus:border-blue-500'}
    `;

    return (
      <div className="space-y-2">
        {label && (
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-200">
            {label}
          </label>
        )}
        <div className="relative">
          <input
            type={type}
            className={twMerge(
              baseStyles,
              'placeholder:text-gray-400 dark:placeholder:text-gray-600',
              className
            )}
            ref={ref}
            {...props}
          />
          {/* Animated focus ring */}
          <div className="absolute inset-0 transition-opacity opacity-0 pointer-events-none peer-focus:opacity-100">
            <div className="absolute inset-0 transition-transform scale-95 bg-blue-50 dark:bg-blue-500/10 rounded-xl" />
          </div>
        </div>
        {/* Error message */}
        {error && (
          <p className="text-sm text-red-500 dark:text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input; 