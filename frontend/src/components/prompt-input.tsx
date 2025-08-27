"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Send, Sparkles, Zap } from "lucide-react";
import { motion } from "framer-motion";

const promptSchema = z.object({
  prompt: z
    .string()
    .min(10, "Prompt must be at least 10 characters long")
    .max(2000, "Prompt must be less than 2000 characters")
    .refine((val) => val.trim().length > 0, "Prompt cannot be empty")
    .refine(
      (val) => !/(password|api[_\s]?key|secret)/i.test(val.toLowerCase()),
      "Prompt should not contain sensitive information"
    ),
});

type PromptFormData = z.infer<typeof promptSchema>;

interface PromptInputProps {
  onSubmit?: (prompt: string) => Promise<void> | void;
  placeholder?: string;
  disabled?: boolean;
  maxLength?: number;
  showCharCount?: boolean;
  autoFocus?: boolean;
  theme?: 'light' | 'dark';
}

export function PromptInput({ 
  onSubmit, 
  placeholder = "Describe what you want to build...", 
  disabled = false,
  maxLength = 2000,
  showCharCount = true,
  autoFocus = true,
  theme = 'light'
}: PromptInputProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [charCount, setCharCount] = useState(0);
  const [inputFocused, setInputFocused] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<PromptFormData>({
    resolver: zodResolver(promptSchema),
    defaultValues: {
      prompt: "",
    },
  });

  const promptValue = watch("prompt");

  React.useEffect(() => {
    setCharCount(promptValue?.length || 0);
  }, [promptValue]);

  const handleFocus = () => {
    setInputFocused(true);
  };

  const handleBlur = () => {
    setInputFocused(false);
  };

  const handleFormSubmit = async (data: PromptFormData) => {
    if (isSubmitting) return;

    setIsSubmitting(true);
    try {
      // Call the supervisor workflow API endpoint
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000';
      const response = await fetch(`${apiBaseUrl}/api/v1/supervisor/build`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: data.prompt,
          priority: 1,
          requirements: {
            framework: 'React',
            blockchain: 'Ethereum',
            features: [],
            llm_provider: 'gemini',
            model: 'gemini-pro'
          }
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Supervisor workflow result:', result);
      
      if (onSubmit) {
        await onSubmit(data.prompt);
      }
      reset();
    } catch (error) {
      console.error("Error submitting prompt:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Cmd/Ctrl + Enter
    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit(handleFormSubmit)();
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      className="w-full max-w-5xl mx-auto"
    >
      {/* Header Section */}
      <div className="text-center mb-8">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="flex items-center justify-center gap-3 mb-4"
        >
          <div className="relative">
            <Sparkles className="w-8 h-8 text-blue-600" />
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
              className="absolute -top-1 -right-1 w-3 h-3"
            >
              <Zap className="w-3 h-3 text-purple-500" />
            </motion.div>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800 bg-clip-text text-transparent">
            AI Web3 Builder
          </h2>
        </motion.div>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed"
        >
          Describe your Web3 application idea and watch our AI transform it into reality
        </motion.p>
      </div>

      {/* Main Input Card */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6, delay: 0.3 }}
      >
        <Card className="border-0 shadow-2xl bg-white/80 backdrop-blur-sm hover:shadow-3xl transition-all duration-500 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-blue-50/50 via-white to-purple-50/50 pointer-events-none" />
          <CardContent className="relative p-8 md:p-12">
            <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
              <div className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-2xl blur-xl group-focus-within:blur-2xl transition-all duration-300" />
                <div className="relative">
                  <Textarea
                    {...register("prompt")}
                    placeholder={placeholder}
                    disabled={disabled || isSubmitting}
                    onKeyDown={handleKeyDown}
                    onFocus={handleFocus}
                    onBlur={handleBlur}
                    maxLength={maxLength}
                    autoFocus={autoFocus}
                    className={`min-h-[160px] text-lg leading-relaxed resize-none border-2 rounded-2xl px-6 py-5 transition-all duration-300 backdrop-blur-sm ${inputFocused ? 'ring-4 ring-blue-500/20 border-blue-500' : 'border-gray-200 hover:border-gray-300'} ${theme === 'dark' ? 'bg-gray-900/90 text-white placeholder:text-gray-400' : 'bg-white/90 text-gray-900 placeholder:text-gray-400'}`}
                    error={errors.prompt?.message}
                    aria-label="Describe your Web3 application"
                    aria-describedby="char-count prompt-help"
                  />
                  {showCharCount && (
                    <div 
                      id="char-count"
                      className={`absolute bottom-4 right-4 text-sm font-medium px-2 py-1 rounded-lg backdrop-blur-sm ${theme === 'dark' ? 'bg-gray-800/80 text-gray-300' : 'bg-white/80 text-gray-500'}`}
                    >
                      <span className={charCount > (maxLength * 0.9) ? 'text-orange-500' : charCount > (maxLength * 0.95) ? 'text-red-500' : theme === 'dark' ? 'text-gray-300' : 'text-gray-500'}>
                        {charCount}
                      </span>
                      <span className={theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}>/{maxLength}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {errors.prompt && (
                <motion.div
                  initial={{ opacity: 0, height: 0, y: -10 }}
                  animate={{ opacity: 1, height: "auto", y: 0 }}
                  exit={{ opacity: 0, height: 0, y: -10 }}
                  className={`flex items-center gap-2 text-sm font-medium px-4 py-3 rounded-xl border ${theme === 'dark' ? 'bg-red-900/20 text-red-400 border-red-800/30' : 'bg-red-50 text-red-600 border-red-200'}`}
                  role="alert"
                  aria-live="polite"
                >
                  <div className={`w-2 h-2 rounded-full ${theme === 'dark' ? 'bg-red-400' : 'bg-red-500'}`} />
                  {errors.prompt.message}
                </motion.div>
              )}

              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
                <div 
                  id="prompt-help"
                  className={`flex items-center gap-2 text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}
                >
                  <div className="hidden sm:flex items-center gap-1">
                    <kbd className={`px-2 py-1 rounded-md text-xs font-mono border ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-700'}`}>
                      {navigator.platform.indexOf('Mac') === 0 ? '⌘' : 'Ctrl'}
                    </kbd>
                    <span>+</span>
                    <kbd className={`px-2 py-1 rounded-md text-xs font-mono border ${theme === 'dark' ? 'bg-gray-800 border-gray-700 text-gray-300' : 'bg-gray-100 border-gray-200 text-gray-700'}`}>
                      Enter
                    </kbd>
                    <span className="ml-1">to submit</span>
                  </div>
                  <div className={`sm:hidden text-xs ${theme === 'dark' ? 'text-gray-500' : 'text-gray-400'}`}>
                    Tap the button below to submit
                  </div>
                </div>
                
                <motion.div
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <Button
                    type="submit"
                    disabled={disabled || isSubmitting || !promptValue?.trim()}
                    size="lg"
                    className={`font-semibold px-8 py-4 rounded-2xl shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 min-w-[140px] group ${theme === 'dark' 
                      ? 'bg-gradient-to-r from-blue-700 via-indigo-700 to-purple-800 hover:from-blue-800 hover:via-indigo-800 hover:to-purple-900 text-white' 
                      : 'bg-gradient-to-r from-blue-600 via-blue-700 to-purple-700 hover:from-blue-700 hover:via-purple-700 hover:to-purple-800 text-white'}`}
                    aria-label={isSubmitting ? 'Building your application' : 'Build Web3 application'}
                  >
                    {isSubmitting ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        <span>Building...</span>
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5 mr-2 group-hover:translate-x-0.5 transition-transform duration-200" />
                        <span>Build App</span>
                      </>
                    )}
                  </Button>
                </motion.div>
              </div>
            </form>
          </CardContent>
        </Card>
      </motion.div>

      {/* Additional Help Text */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.8 }}
        className="text-center mt-6"
      >
        <p className={`text-sm max-w-md mx-auto ${theme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
          Be specific about features, blockchain networks, and functionality for best results
        </p>
      </motion.div>
    </motion.div>
  );
}