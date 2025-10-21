// src/components/emoji-picker.jsx
import React, { useState, useRef, useEffect } from 'react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Smile, Loader2 } from 'lucide-react';
// This static import can cause build issues in some environments. We'll import it dynamically instead.
// import data from '@emoji-mart/data';
import Picker from '@emoji-mart/react';

export function EmojiPicker({ onSelect }) {
  const [isOpen, setIsOpen] = useState(false);
  const [emojiData, setEmojiData] = useState(null);
  const popoverRef = useRef(null);

  // Dynamically import emoji data only when the popover is about to open for the first time.
  useEffect(() => {
    if (isOpen && !emojiData) {
      import('@emoji-mart/data').then(module => setEmojiData(module.default));
    }
  }, [isOpen, emojiData]);

  const handleEmojiSelect = (emoji) => {
    onSelect(emoji.native);
    setIsOpen(false);
  };

  // Close when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="rounded-full p-2 hover:bg-muted transition-colors"
          onClick={() => setIsOpen(!isOpen)}
        >
          <Smile className="h-5 w-5 text-muted-foreground" />
        </button>
      </PopoverTrigger>
      <PopoverContent 
        ref={popoverRef}
        className="w-auto p-0 border-0 shadow-lg"
        align="start"
      >
        {emojiData ? (
          <Picker
            data={emojiData}
            onEmojiSelect={handleEmojiSelect}
            theme="light"
            previewPosition="none"
            searchPosition="none"
            skinTonePosition="none"
            perLine={8}
            emojiSize={24}
            emojiButtonSize={36}
            navPosition="none"
            dynamicWidth={true}
          />
        ) : (
          <div className="flex items-center justify-center h-[436px] w-[352px]">
            <Loader2 className="h-8 w-8 text-muted-foreground animate-spin" />
          </div>
        )}
      </PopoverContent>
    </Popover>
  );
}