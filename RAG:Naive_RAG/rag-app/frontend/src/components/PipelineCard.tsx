import React, { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface PipelineCardProps {
  title: string;
  icon: ReactNode;
  isActive: boolean;
  isCompleted: boolean;
  latency?: number;
  children?: ReactNode;
}

export function PipelineCard({ title, icon, isActive, isCompleted, latency, children }: PipelineCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className={cn(
        "relative p-5 rounded-xl border transition-all duration-300",
        isActive
          ? "bg-primary/10 border-primary shadow-[0_0_15px_rgba(59,130,246,0.5)] dark:shadow-[0_0_15px_rgba(59,130,246,0.3)]"
          : isCompleted
          ? "bg-secondary/50 border-secondary"
          : "bg-card border-border opacity-60"
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            isActive ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
          )}>
            {icon}
          </div>
          <h3 className="font-semibold text-lg">{title}</h3>
        </div>
        {latency !== undefined && (
          <span className="text-xs font-mono bg-muted px-2 py-1 rounded text-muted-foreground">
            {latency}ms
          </span>
        )}
      </div>
      
      {children && (
        <motion.div 
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          className="mt-4 text-sm text-muted-foreground overflow-hidden"
        >
          {children}
        </motion.div>
      )}
    </motion.div>
  );
}
