interface KogniiThinkingIconProps {
  className?: string;
  size?: number;
}

export function KogniiThinkingIcon({ className = "w-4 h-4", size }: KogniiThinkingIconProps) {
  const style = size ? { width: size, height: size } : {};
  
  return (
    <div 
      className={`${className} rounded-full kognii-thinking-gradient`}
      style={style}
    />
  );
}