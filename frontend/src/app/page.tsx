"use client";

import React, { useState, useRef } from "react";
import { Header } from "@/components/header";
import { HeroSection } from "@/components/hero-section";
import { PromptInput } from "@/components/prompt-input";
import { motion } from "framer-motion";

export default function Home() {
  const [showPromptInput, setShowPromptInput] = useState(false);
  const promptSectionRef = useRef<HTMLDivElement>(null);

  const handleGetStarted = () => {
    setShowPromptInput(true);
    setTimeout(() => {
      promptSectionRef.current?.scrollIntoView({ 
        behavior: "smooth", 
        block: "center" 
      });
    }, 100);
  };

  const handlePromptSubmit = async (prompt: string) => {
    console.log("Submitted prompt:", prompt);
    // TODO: Integrate with backend API
    // This will be connected to the FastAPI backend later
    
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    alert(`Prompt submitted: ${prompt.substring(0, 50)}...`);
  };

  return (
    <div className="min-h-screen">
      <Header onGetStarted={handleGetStarted} />
      
      <main>
        {/* Hero Section */}
        <HeroSection onGetStarted={handleGetStarted} />
        
        {/* Prompt Input Section */}
        {showPromptInput && (
          <motion.section
            ref={promptSectionRef}
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="py-20 bg-gray-50"
          >
            <div className="container mx-auto px-4">
              <div className="text-center mb-12">
                <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                  Describe Your Web3 App
                </h2>
                <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                  Tell us what you want to build, and our AI will generate a complete Web3 application for you.
                </p>
              </div>
              
              <PromptInput 
                onSubmit={handlePromptSubmit}
                placeholder="I want to build a decentralized marketplace where users can buy and sell NFTs with custom royalty settings..."
              />
            </div>
          </motion.section>
        )}
        

      </main>
      
      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4">
          <div className="text-center">
            <h3 className="text-2xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Web3Builder
            </h3>
            <p className="text-gray-400 mb-6">
              Build the future of the web with AI-powered Web3 development
            </p>
            <div className="flex justify-center space-x-6">
              <a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">
                Privacy Policy
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">
                Terms of Service
              </a>
              <a href="#" className="text-gray-400 hover:text-white transition-colors duration-200">
                Contact
              </a>
            </div>
            <div className="mt-8 pt-8 border-t border-gray-800 text-gray-500">
              © 2024 Web3Builder. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
