import React, { useEffect, useRef } from 'react';

interface AudioVisualizerProps {
  active: boolean;
  stream: MediaStream | null;
  width?: number;
  height?: number;
}

const AudioVisualizer: React.FC<AudioVisualizerProps> = ({ 
  active, 
  stream, 
  width = 700, 
  height = 120 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);

  useEffect(() => {
    if (!active || !stream) {
      // Stop animation and clean up
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
        animationRef.current = null;
      }
      
      // Clean up audio context
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
        analyserRef.current = null;
      }
      
      // Clear canvas
      if (canvasRef.current) {
        const ctx = canvasRef.current.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, width, height);
        }
      }
      
      return;
    }

    // Setup audio context and analyser
    try {
      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const source = audioContext.createMediaStreamSource(stream);
      
      analyser.fftSize = 256;
      source.connect(analyser);
      
      audioContextRef.current = audioContext;
      analyserRef.current = analyser;
      
      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);
      
      const draw = () => {
        if (!active || !analyserRef.current) return;
        
        animationRef.current = requestAnimationFrame(draw);
        
        analyserRef.current.getByteFrequencyData(dataArray);
        
        const canvas = canvasRef.current;
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        ctx.clearRect(0, 0, width, height);
        
        const barWidth = (width / bufferLength) * 2.5;
        let x = 0;
        
        for (let i = 0; i < bufferLength; i++) {
          const barHeight = (dataArray[i] / 255) * height;
          
          const gradient = ctx.createLinearGradient(0, height - barHeight, 0, height);
          gradient.addColorStop(0, '#10b981');
          gradient.addColorStop(1, '#34d399');
          
          ctx.fillStyle = gradient;
          ctx.fillRect(x, height - barHeight, barWidth, barHeight);
          
          x += barWidth + 1;
        }
      };
      
      draw();
    } catch (error) {
      console.error('Error setting up audio visualization:', error);
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, [active, stream, width, height]);

  return (
    <div className="w-full flex justify-center">
      <div className="w-full max-w-[800px] rounded-2xl overflow-hidden border-2 border-slate-200 bg-slate-900">
        <canvas
          ref={canvasRef}
          width={width}
          height={height}
          className="w-full h-auto"
          style={{ maxWidth: '100%', display: 'block' }}
        />
      </div>
    </div>
  );
};

export default AudioVisualizer;

