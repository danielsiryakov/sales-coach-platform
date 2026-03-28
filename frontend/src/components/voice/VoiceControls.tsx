'use client';

import { PhoneOff, Mic, MicOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface VoiceControlsProps {
  isCapturing: boolean;
  onEndCall: () => void;
}

export function VoiceControls({ isCapturing, onEndCall }: VoiceControlsProps) {
  return (
    <div className="bg-gray-800 border-t border-gray-700 px-6 py-4">
      <div className="flex items-center justify-center space-x-6">
        {/* Microphone indicator */}
        <div className={cn(
          'flex items-center px-4 py-2 rounded-full',
          isCapturing ? 'bg-green-900 text-green-400' : 'bg-gray-700 text-gray-400'
        )}>
          {isCapturing ? (
            <>
              <Mic className="w-5 h-5 mr-2 animate-pulse" />
              <span className="text-sm font-medium">Speaking</span>
            </>
          ) : (
            <>
              <MicOff className="w-5 h-5 mr-2" />
              <span className="text-sm font-medium">Muted</span>
            </>
          )}
        </div>

        {/* End call button */}
        <button
          onClick={onEndCall}
          className="flex items-center px-8 py-3 bg-red-600 text-white rounded-full font-semibold hover:bg-red-500 transition-colors"
        >
          <PhoneOff className="w-5 h-5 mr-2" />
          End Call
        </button>
      </div>
    </div>
  );
}
