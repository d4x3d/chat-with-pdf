'use client';

import { HTMLAttributes } from 'react';
import { twMerge } from 'tailwind-merge';

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'glass';
}

const Card = ({ className, children, variant = 'default', ...props }: CardProps) => {
  // Base styles for the card
  const baseStyles = 'rounded-2xl p-6 transition-all duration-200';
  
  // Variant styles
  const variants = {
    default: 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700',
    glass: 'backdrop-blur-lg bg-white/50 dark:bg-gray-800/50 border border-white/20 dark:border-gray-700/30'
  };

  return (
    <div
      className={twMerge(
        baseStyles,
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default Card; 