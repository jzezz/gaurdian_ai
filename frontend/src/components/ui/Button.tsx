import { motion } from 'framer-motion';

export const Button = ({ children, onClick, variant = 'primary', className = '' }: any) => {
  const base = "px-6 py-2 rounded-full font-medium transition-all duration-200";
  const variants = {
    primary: "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20",
    secondary: "bg-neutral-800 hover:bg-neutral-700 text-neutral-200"
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${base} ${variants[variant as keyof typeof variants]} ${className}`}
      onClick={onClick}
    >
      {children}
    </motion.button>
  );
};
