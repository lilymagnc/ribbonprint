import { useState, useEffect, useRef } from 'react';
import { 
  Printer, 
  Settings, 
  Ruler, 
  Type,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ==========================================
// Constants & Config
// ==========================================
const FONTS = [
  { value: 'font-noto-serif', label: 'Noto Serif (명조)' },
  { value: 'font-noto-sans', label: 'Noto Sans (고딕)' },
  { value: 'font-nanum-myeongjo', label: '나눔명조' },
  { value: 'font-nanum-gothic', label: '나눔고딕' },
];

const RIBBON_TYPES = [
  { id: 'bouquet', name: '꽃다발 38x400mm', width: 38, lace: 5, length: 400, marginTop: 80, marginBottom: 50, fontSize: 30 },
  { id: 'oriental_45', name: '동양란 45x450mm', width: 45, lace: 7, length: 450, marginTop: 100, marginBottom: 50, fontSize: 35 },
  { id: 'oriental_50', name: '동양란 50x500mm', width: 50, lace: 10, length: 500, marginTop: 120, marginBottom: 80, fontSize: 40 },
  { id: 'orchid_55', name: '동/서양란 55x500mm', width: 55, lace: 10, length: 500, marginTop: 120, marginBottom: 80, fontSize: 42 },
  { id: 'western_60', name: '서양란 60/65x700mm', width: 60, lace: 10, length: 700, marginTop: 150, marginBottom: 100, fontSize: 45 },
  { id: 'movie_70', name: '영화(중) 70x750mm', width: 70, lace: 10, length: 750, marginTop: 150, marginBottom: 100, fontSize: 55 },
  { id: 'basket_95', name: '장바구니 95x1000mm', width: 95, lace: 10, length: 1000, marginTop: 180, marginBottom: 130, fontSize: 75 },
  { id: 'pot_small', name: '화분 소 105/110x1100mm', width: 105, lace: 23, length: 1100, marginTop: 200, marginBottom: 150, fontSize: 80 },
  { id: 'pot_medium', name: '화분 중 135x1500mm', width: 135, lace: 23, length: 1500, marginTop: 300, marginBottom: 200, fontSize: 100 },
  { id: 'pot_large', name: '화분 대 150x1800mm', width: 150, lace: 23, length: 1800, marginTop: 350, marginBottom: 350, fontSize: 110 },
  { id: 'wreath_1', name: '근조 1단 115x1200mm', width: 115, lace: 23, length: 1200, marginTop: 250, marginBottom: 150, fontSize: 90 },
  { id: 'wreath_2', name: '근조 2단 135x1700mm', width: 135, lace: 23, length: 1700, marginTop: 300, marginBottom: 200, fontSize: 100 },
  { id: 'wreath_3', name: '근조 3단 165x2200mm', width: 165, lace: 23, length: 2200, marginTop: 400, marginBottom: 300, fontSize: 130 },
  { id: 'celebration_3', name: '축화 3단 165x2200mm', width: 165, lace: 23, length: 2200, marginTop: 400, marginBottom: 300, fontSize: 130 },
];

const PHRASE_BANK = [
  '祝 發 展',
  '祝 開 業',
  '祝 結 婚',
  '謹 弔',
  '祝 移 轉',
  '祝 創 立',
  '祝 就 任',
  '祝 昇 進',
];

const SYMBOL_BANK = ['★', '(주)', '(유)', '♥', '♣', '♠', '◆', '▶', '◀', '※', '✝', '卍'];

// ==========================================
// Parsing & Types
// ==========================================
interface CharNode {
  type: 'char' | 'bracket' | 'split' | 'fullwidth' | 'space';
  content: string;
  leftContent?: string;
  rightContent?: string;
  isRotated?: boolean;
  id: string; // for stable state tracking
}

const parseRibbonLine = (text: string, baseId: string, rotatedIds: Set<string>): CharNode[] => {
  const nodes: CharNode[] = [];
  const regex = /\[([^/\]]+)\/([^\]]+)\]|\[([^\]]+)\]|\((주|유)\)|( )|./gu;
  let match;
  let charIndex = 0;

  while ((match = regex.exec(text)) !== null) {
    const id = `${baseId}-${charIndex++}`;
    const raw = match[0];

    if (match[1] && match[2]) {
      // [left/right]
      nodes.push({ type: 'split', content: raw, leftContent: match[1], rightContent: match[2], id });
    } else if (match[3]) {
      // [bracket]
      nodes.push({ type: 'bracket', content: match[3], id });
    } else if (match[4]) {
      // (주)
      nodes.push({ type: 'fullwidth', content: raw, id });
    } else if (match[5]) {
      // space
      nodes.push({ type: 'space', content: raw, id });
    } else {
      // is this naturally rotated? (English/Numbers)
      const isAlphanumeric = /[A-Za-z0-9]/.test(raw);
      // user override check
      const isRotated = rotatedIds.has(id) ? !isAlphanumeric : isAlphanumeric;
      
      nodes.push({ type: 'char', content: raw, id, isRotated });
    }
  }
  return nodes;
};

// ==========================================
// Ribbon Canvas Component
// ==========================================
interface RibbonCanvasProps {
  text: string;
  font: string;
  ratioX: number;    // horizontal percentage scale
  ratioY: number;    // vertical percentage scale
  width: number;
  lace: number;
  length: number;
  marginTop: number;
  marginBottom: number;
  rotatedIds: Set<string>;
  onCharClick: (id: string) => void;
  scaleRatio: number; // rendering scale
  zoom: number;      // current zoom level to compensate UI scale
  side?: 'left' | 'right'; 
}

const RibbonCanvas = ({ 
  text, font, ratioX, ratioY, width, lace, length, marginTop, marginBottom, 
  rotatedIds, onCharClick, scaleRatio, zoom, side = 'left'
}: RibbonCanvasProps) => {
  // Parse lines
  const lines = text.split('\n').filter(l => l.trim() !== '');

  // Base font size exactly matches the ribbon printable width in pixels
  const printableWidthPX = Math.max(10, width - (lace * 2)) * scaleRatio;
  const baseFontSizePX = printableWidthPX * 1.15; // Visual 100% Fill (accounts for font margins)

  const scaleXObj = ratioX / 100;
  const scaleYObj = ratioY / 100;

  // Actual block dimensions
  const actualFontSize = baseFontSizePX * scaleYObj;
  const fontScaleX = scaleYObj === 0 ? 1 : scaleXObj / scaleYObj;

  return (
    <div 
      className="relative flex justify-center"
      style={{
        width: `${width * scaleRatio}px`,
        height: `${length * scaleRatio}px`,
      }}
    >
      {/* Visual Ruler Outside the Ribbon */}
      <div 
        className={cn(
          "absolute top-0 bottom-0 flex flex-col justify-between font-mono py-1 z-10 pointer-events-none",
          side === 'left' ? "items-end pr-2" : "items-start pl-2"
        )}
        style={{
          width: `${60 / zoom}px`,
          [side === 'left' ? 'right' : 'left']: '100%',
          [side === 'left' ? 'marginRight' : 'marginLeft']: `${20 / zoom}px`
        }}
      >
        <span style={{ transform: `scale(${1/zoom})`, transformOrigin: side === 'left' ? 'right top' : 'left top', fontSize: '14px', color: '#94a3b8', fontWeight: 'bold' }}>0</span>
        <div style={{ width: `${1/zoom}px` }} className={cn("h-full bg-gray-500/50 absolute top-0 bottom-0", side === 'left' ? "right-0" : "left-0")}></div>
        <span style={{ transform: `scale(${1/zoom})`, transformOrigin: side === 'left' ? 'right bottom' : 'left bottom', fontSize: '14px', color: '#94a3b8', fontWeight: 'bold' }}>{length}</span>
      </div>

      {/* Margins Indicators Outside the Ribbon */}
      <div 
        className={cn("absolute border-red-500/70 z-20 pointer-events-none", side === 'left' ? "right-full" : "left-full")}
        style={{ 
          top: `${marginTop * scaleRatio}px`,
          borderTopWidth: `${1/zoom}px`,
          borderTopStyle: 'dashed',
          width: `${120 / zoom}px`, // Constant line length on screen
          [side === 'left' ? 'marginRight' : 'marginLeft']: '0px'
        }}
      >
        <span 
          className={cn("absolute text-[14px] text-red-500 font-black bg-[#0f172a] px-1 whitespace-nowrap", side === 'left' ? "left-0" : "right-0")}
          style={{ 
            transform: `scale(${1/zoom})`, 
            transformOrigin: side === 'left' ? 'left bottom' : 'right bottom',
            bottom: `${0.3/zoom}rem`
          }}
        >
          상단여백 {marginTop}
        </span>
      </div>

      <div 
        className={cn("absolute border-red-500/70 z-20 pointer-events-none", side === 'left' ? "right-full" : "left-full")}
        style={{ 
          bottom: `${marginBottom * scaleRatio}px`,
          borderBottomWidth: `${1/zoom}px`,
          borderBottomStyle: 'dashed',
          width: `${120 / zoom}px`, // Constant line length on screen
          [side === 'left' ? 'marginRight' : 'marginLeft']: '0px'
        }}
      >
        <span 
          className={cn("absolute text-[14px] text-red-500 font-black bg-[#0f172a] px-1 whitespace-nowrap", side === 'left' ? "left-0" : "right-0")}
          style={{ 
            transform: `scale(${1/zoom})`, 
            transformOrigin: side === 'left' ? 'left top' : 'right top',
            top: `${0.3/zoom}rem`
          }}
        >
          하단여백 {marginBottom}
        </span>
      </div>

      {/* Ribbon Body */}
      <div className="bg-white ribbon-texture shadow-2xl relative overflow-hidden flex flex-col items-center" style={{ width: '100%', height: '100%' }}>
        
        {/* Lace Effects */}
        {lace > 0 && (
          <>
            <div className="absolute left-0 top-0 bottom-0 border-r border-[#00000010] flex flex-col overflow-hidden" style={{ width: `${lace * scaleRatio}px` }}>
               <div className="flex-1 w-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-amber-200/20 to-transparent" style={{ backgroundSize: '4px 4px' }} />
            </div>
            <div className="absolute right-0 top-0 bottom-0 border-l border-[#00000010] flex flex-col overflow-hidden" style={{ width: `${lace * scaleRatio}px` }}>
               <div className="flex-1 w-full bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-amber-200/20 to-transparent" style={{ backgroundSize: '4px 4px' }} />
            </div>
          </>
        )}

        {/* Text Container boundaries = exact margins */}
        <div 
          className="absolute left-0 right-0 flex flex-row-reverse justify-center gap-4"
          style={{
            top: `${marginTop * scaleRatio}px`,
            bottom: `${marginBottom * scaleRatio}px`,
          }}
        >
          {lines.map((line, lIdx) => {
            const nodes = parseRibbonLine(line, `L${lIdx}`, rotatedIds);
            
            // Mathematically calculate required height (Full Fit logic)
            const requiredHeight = nodes.reduce((sum, n) => {
               if (n.type === 'space') return sum + (actualFontSize * 0.65);

               // Add buffer spacing for bracketed/split nodes (Law 2 & 3)
               const nodeSpacing = (n.type === 'bracket' || n.type === 'split') ? (actualFontSize * 0.5) : 0;

               if (n.type === 'split') {
                 const leftL = n.leftContent?.length || 0;
                 const rightL = n.rightContent?.length || 0;
                 return sum + (Math.max(leftL, rightL) * actualFontSize * 0.65) + nodeSpacing;
               }
               if (n.type === 'bracket') {
                 return sum + (n.content.length * actualFontSize * 0.65) + nodeSpacing;
               }
               return sum + actualFontSize;
            }, 0);
            
            const availableHeight = Math.max(0, (length - marginTop - marginBottom) * scaleRatio);
            let squashRatio = 1;
            if (requiredHeight > availableHeight && availableHeight > 0) {
              squashRatio = availableHeight / requiredHeight;
            }

            return (
              <div 
                key={lIdx} 
                className={cn(font, "flex flex-col items-center shrink-0 w-max text-black font-bold whitespace-nowrap")}
                style={{
                  height: squashRatio < 1 ? `${requiredHeight}px` : '100%',
                  transform: squashRatio < 1 ? `scaleY(${squashRatio})` : 'none',
                  transformOrigin: 'top center',
                  justifyContent: nodes.length === 1 ? 'center' : 'space-between'
                }}
              >
                {nodes.map(node => {
                  const nodeH = actualFontSize;
                  const nodeW = baseFontSizePX * scaleXObj;

                  // Law 5: Space 65% Height
                  if (node.type === 'space') {
                    return <div key={node.id} style={{ height: `${nodeH * 0.65}px`, width: nodeW }} />;
                  }

                  // Law 4: Fullwidth
                  if (node.type === 'fullwidth') {
                    return (
                      <div key={node.id} className="flex justify-center items-center shrink-0" style={{ height: actualFontSize, width: nodeW }}>
                        <span style={{ fontSize: `${actualFontSize * 0.85}px`, transform: `scaleX(${fontScaleX})`, display: 'inline-block', letterSpacing: '-0.1em' }}>{node.content}</span>
                      </div>
                    );
                  }

                  // Law 2: Special Bracket Multi-line (e.g. [HongGilDong])
                  if (node.type === 'bracket') {
                    const chars = node.content.split('');
                    const blockHeight = chars.length * actualFontSize * 0.65; 
                    
                    return (
                      <div key={node.id} className={cn("flex flex-col items-center shrink-0 leading-none py-2", chars.length > 1 ? "justify-between" : "justify-center")} style={{ height: blockHeight + (actualFontSize * 0.5), width: nodeW }}>
                        {chars.map((c, i) => (
                           <span key={i} style={{ 
                             fontSize: `${nodeW * 0.65}px`, // 65% reduction as requested
                             lineHeight: 1,
                             display: 'inline-block',
                             fontWeight: 'bold'
                           }}>{c}</span>
                        ))}
                      </div>
                    );
                  }

                  // Law 3: Split Columns (Parallel vertical stacks)
                  if (node.type === 'split') {
                    const leftChars = node.leftContent?.split('') || [];
                    const rightChars = node.rightContent?.split('') || [];
                    const maxLen = Math.max(leftChars.length, rightChars.length);
                    const blockHeight = maxLen * actualFontSize * 0.65;

                    return (
                      <div key={node.id} className="flex flex-row items-center justify-center shrink-0 py-2" style={{ height: blockHeight + (actualFontSize * 0.5), width: nodeW }}>
                         <div className={cn("flex flex-col items-center h-full flex-1", leftChars.length > 1 ? "justify-between" : "justify-center")}>
                           {leftChars.map((char, i) => (
                             <div key={i} className="flex items-center justify-center shrink-0" style={{ height: blockHeight / maxLen, width: '100%' }}>
                               <span style={{ 
                                 fontSize: `${nodeW * 0.65 * 0.45}px`, // 65% of half width
                                 display: 'inline-block',
                                 lineHeight: 1
                               }}>{char}</span>
                             </div>
                           ))}
                         </div>
                         <div className={cn("flex flex-col items-center h-full flex-1", rightChars.length > 1 ? "justify-between" : "justify-center")}>
                           {rightChars.map((char, i) => (
                             <div key={i} className="flex items-center justify-center shrink-0" style={{ height: blockHeight / maxLen, width: '100%' }}>
                               <span style={{ 
                                 fontSize: `${nodeW * 0.65 * 0.45}px`, // 65% of half width
                                 display: 'inline-block',
                                 lineHeight: 1
                               }}>{char}</span>
                             </div>
                           ))}
                         </div>
                      </div>
                    );
                  }

                  // Law 1: Normal / 90-degree Rotation
                  return (
                    <div 
                      key={node.id} 
                      className="cursor-pointer hover:text-blue-600 transition-colors flex justify-center items-center shrink-0 leading-none"
                      style={{ height: nodeH, width: nodeW }}
                      onClick={() => onCharClick(node.id)}
                    >
                      <span style={{ 
                        fontSize: nodeH,
                        transform: `scaleX(${fontScaleX}) ${node.isRotated ? 'rotate(90deg)' : ''}`,
                        display: 'inline-block'
                      }}>
                        {node.content}
                      </span>
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};


// ==========================================
// Main Application
// ==========================================
export default function App() {
  const mainRef = useRef<HTMLElement>(null);

  // Specs State
  const [ribbonType, setRibbonType] = useState(RIBBON_TYPES[0].id);
  const [length, setLength] = useState(400);
  const [width, setWidth] = useState(38);
  const [lace, setLace] = useState(5);
  const [marginTop, setMarginTop] = useState(80);
  const [marginBottom, setMarginBottom] = useState(50);

  // Left Ribbon State
  const [leftText, setLeftText] = useState('祝發展');
  const [leftFont, setLeftFont] = useState(FONTS[3].value);
  const [leftRatioX, setLeftRatioX] = useState(100);
  const [leftRatioY, setLeftRatioY] = useState(100);
  const [leftRotated, setLeftRotated] = useState<Set<string>>(new Set());

  // Right Ribbon State
  const [rightText, setRightText] = useState('(주)디자인스튜디오 대표이사 [홍길동]');
  const [rightFont, setRightFont] = useState(FONTS[3].value);
  const [rightRatioX, setRightRatioX] = useState(100);
  const [rightRatioY, setRightRatioY] = useState(100);
  const [rightRotated, setRightRotated] = useState<Set<string>>(new Set());

  // UI State
  const [activeSide, setActiveSide] = useState<'left'|'right'>('left');
  const [zoom, setZoom] = useState(0.4);

  // Auto-Zoom Calculation
  useEffect(() => {
    if (mainRef.current && length > 0) {
      const availableH = mainRef.current.clientHeight - 100; // top/bottom padding 50px each
      const targetH = length * 2; // using scaleRatio = 2 internally relative to mm lengths
      if (targetH > 0) {
        setZoom(Math.min(2.0, availableH / targetH));
      }
    }
  }, [length, ribbonType]); // re-run when content changes

  useEffect(() => {
    const defaultSpecs = RIBBON_TYPES.find(t => t.id === ribbonType);
    if (defaultSpecs) {
      setWidth(defaultSpecs.width);
      setLace(defaultSpecs.lace);
      setLength(defaultSpecs.length);
      setMarginTop(defaultSpecs.marginTop); 
      setMarginBottom(defaultSpecs.marginBottom);
    }
  }, [ribbonType]);

  const insertSymbol = (sym: string) => {
    if (activeSide === 'left') setLeftText(prev => prev + sym);
    else setRightText(prev => prev + sym);
  };

  const toggleRotation = (id: string, side: 'left'|'right') => {
    const toggleSet = (prev: Set<string>) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    };
    if (side === 'left') setLeftRotated(toggleSet);
    else setRightRotated(toggleSet);
  };

  return (
    <div className="flex bg-slate-900 text-slate-200 h-screen w-screen overflow-hidden text-sm">
      
      {/* 1. Left Panel: Settings */}
      <aside className="w-80 glass-panel flex flex-col shrink-0 z-10 p-5 overflow-y-auto space-y-6">
        <div>
          <h1 className="text-xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-indigo-400 flex items-center gap-2 mb-1">
            <Ruler size={24} className="text-blue-500" />
            RibbonMaker PRO
          </h1>
          <p className="text-xs text-slate-400 font-mono">Build 2026.03 (Full-Fit Engine)</p>
        </div>

        {/* Specs */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-slate-300 font-bold mb-2 border-b border-slate-700 pb-2">
            <Settings size={16} /> 하드웨어 규격
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">프리셋</label>
            <select 
              value={ribbonType} 
              onChange={e => setRibbonType(e.target.value)}
              className="w-full p-2 rounded-lg text-sm"
            >
              {RIBBON_TYPES.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">폭 (mm)</label>
              <input type="number" value={width} onChange={e => setWidth(Number(e.target.value))} className="w-full p-2 rounded-lg text-sm text-center font-mono" />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">길이 (mm)</label>
              <input type="number" value={length} onChange={e => setLength(Number(e.target.value))} className="w-full p-2 rounded-lg text-sm text-center font-mono" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">상단</label>
              <input type="number" value={marginTop} onChange={e => setMarginTop(Number(e.target.value))} className="w-full p-2 rounded-lg text-sm text-center font-mono" />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">하단</label>
              <input type="number" value={marginBottom} onChange={e => setMarginBottom(Number(e.target.value))} className="w-full p-2 rounded-lg text-sm text-center font-mono" />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">레이스</label>
              <input type="number" value={lace} onChange={e => setLace(Number(e.target.value))} className="w-full p-2 rounded-lg text-sm text-center font-mono" />
            </div>
          </div>
        </div>

        {/* Left Ribbon Detail */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-slate-300 font-bold mb-1 border-b border-slate-700 pb-2">
            <div className="flex items-center gap-2"><Type size={16} /> 좌측 리본 (경조사)</div>
            <button 
              onClick={() => setActiveSide('left')}
              className={cn("text-[10px] px-2 py-0.5 rounded font-bold transition-all", activeSide === 'left' ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-400")}
            >ACTIVE</button>
          </div>
          <input 
            type="text"
            value={leftText} 
            onChange={e => setLeftText(e.target.value)}
            onFocus={() => setActiveSide('left')}
            className={cn("w-full p-2 rounded-lg text-sm leading-tight focus:ring-2", leftFont)}
            placeholder="경조사 입력"
          />
          <div className="flex flex-col gap-2">
            <select value={leftFont} onChange={e => setLeftFont(e.target.value)} className="w-full p-2 rounded-lg text-sm bg-slate-800 border-slate-700 text-white">
              {FONTS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
                 <span className="bg-slate-700 text-xs text-slate-300 px-2 flex items-center justify-center shrink-0 w-12">가로</span>
                 <input type="number" value={leftRatioX} onChange={e => setLeftRatioX(Number(e.target.value))} className="w-full p-1.5 text-sm text-center font-mono bg-transparent outline-none text-white" />
              </div>
              <div className="flex bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
                 <span className="bg-slate-700 text-xs text-slate-300 px-2 flex items-center justify-center shrink-0 w-12">세로</span>
                 <input type="number" value={leftRatioY} onChange={e => setLeftRatioY(Number(e.target.value))} className="w-full p-1.5 text-sm text-center font-mono bg-transparent outline-none text-white" />
              </div>
            </div>
          </div>
        </div>

        {/* Right Ribbon Detail */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-slate-300 font-bold mb-1 border-b border-slate-700 pb-2">
            <div className="flex items-center gap-2"><Type size={16} /> 우측 리본 (보내는이)</div>
            <button 
              onClick={() => setActiveSide('right')}
              className={cn("text-[10px] px-2 py-0.5 rounded font-bold transition-all", activeSide === 'right' ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-400")}
            >ACTIVE</button>
          </div>
          <input 
            type="text"
            value={rightText} 
            onChange={e => setRightText(e.target.value)}
            onFocus={() => setActiveSide('right')}
            className={cn("w-full p-2 rounded-lg text-sm leading-tight focus:ring-2", rightFont)}
            placeholder="보내는이 입력"
          />
          <div className="flex flex-col gap-2">
            <select value={rightFont} onChange={e => setRightFont(e.target.value)} className="w-full p-2 rounded-lg text-sm bg-slate-800 border-slate-700 text-white">
              {FONTS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
            </select>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
                 <span className="bg-slate-700 text-xs text-slate-300 px-2 flex items-center justify-center shrink-0 w-12">가로</span>
                 <input type="number" value={rightRatioX} onChange={e => setRightRatioX(Number(e.target.value))} className="w-full p-1.5 text-sm text-center font-mono bg-transparent outline-none text-white" />
              </div>
              <div className="flex bg-slate-800 rounded-lg overflow-hidden border border-slate-700">
                 <span className="bg-slate-700 text-xs text-slate-300 px-2 flex items-center justify-center shrink-0 w-12">세로</span>
                 <input type="number" value={rightRatioY} onChange={e => setRightRatioY(Number(e.target.value))} className="w-full p-1.5 text-sm text-center font-mono bg-transparent outline-none text-white" />
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* 2. Center Panel: Canvas */}
      <main ref={mainRef} className="flex-1 relative flex justify-center items-start overflow-auto p-12 bg-[#0f172a]">
        
        {/* Canvas Area */}
        <div className="flex gap-24 transition-transform duration-300" style={{ transform: `scale(${zoom})`, transformOrigin: 'top center' }}>
          <RibbonCanvas 
            text={leftText} font={leftFont} ratioX={leftRatioX} ratioY={leftRatioY} lace={lace}
            width={width} length={length} marginTop={marginTop} marginBottom={marginBottom}
            rotatedIds={leftRotated} onCharClick={(id) => toggleRotation(id, 'left')}
            scaleRatio={2} zoom={zoom} side="left"
          />
          <RibbonCanvas 
            text={rightText} font={rightFont} ratioX={rightRatioX} ratioY={rightRatioY} lace={lace}
            width={width} length={length} marginTop={marginTop} marginBottom={marginBottom}
            rotatedIds={rightRotated} onCharClick={(id) => toggleRotation(id, 'right')}
            scaleRatio={2} zoom={zoom} side="right"
          />
        </div>

        {/* Floating Actions */}
        <div className="fixed bottom-8 right-[320px] bg-slate-800/80 backdrop-blur-md p-2 rounded-full border border-slate-600 flex gap-2 shadow-2xl z-20">
          <button onClick={() => setZoom(z => Math.max(0.1, z - 0.1))} className="p-2 hover:bg-slate-700 rounded-full transition-colors"><Minimize2 size={18} /></button>
          <div className="px-3 flex items-center justify-center font-mono text-xs">{Math.round(zoom * 100)}%</div>
          <button onClick={() => setZoom(z => Math.min(2.0, z + 0.1))} className="p-2 hover:bg-slate-700 rounded-full transition-colors"><Maximize2 size={18} /></button>
          <div className="w-px h-6 bg-slate-600 my-auto mx-1"></div>
          <button className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-full font-bold transition-all shadow-lg">
            <Printer size={16} /> PRINT
          </button>
        </div>
      </main>

      {/* 3. Right Panel: Banks */}
      <aside className="w-[280px] glass-panel shrink-0 z-10 p-5 overflow-y-auto space-y-6">
        
        <div>
          <h2 className="text-sm font-bold text-slate-300 border-b border-slate-700 pb-2 mb-3">자주 쓰는 상용구</h2>
          <div className="grid grid-cols-2 gap-2">
            {PHRASE_BANK.map(phrase => (
               <button 
                 key={phrase} 
                 onClick={() => {
                   const formatted = phrase.replace(/ /g, '\n');
                   if (activeSide === 'left') setLeftText(formatted);
                   else setRightText(formatted);
                 }}
                 className="bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded py-2 text-xs font-bold transition-colors font-nanum-myeongjo"
               >
                 {phrase}
               </button>
            ))}
          </div>
        </div>

        <div>
          <h2 className="text-sm font-bold text-slate-300 border-b border-slate-700 pb-2 mb-3">특수기호 (Click to Insert)</h2>
          <div className="grid grid-cols-4 gap-2">
            {SYMBOL_BANK.map(sym => (
               <button 
                 key={sym} 
                 onClick={() => insertSymbol(sym)}
                 className="bg-slate-800 hover:bg-brand border border-slate-700 hover:border-brand rounded py-2 text-xs transition-colors"
               >
                 {sym}
               </button>
            ))}
          </div>
        </div>

        <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700 space-y-2 mt-auto">
          <h3 className="text-xs font-bold text-blue-400 mb-2">프리뷰 팁 (7대 법칙)</h3>
          <ul className="text-[10px] text-slate-400 space-y-1 ml-3 list-disc">
            <li>영문/숫자는 자동 회전됩니다. <strong>클릭</strong>하여 수동으로 눕힐 수 있습니다.</li>
            <li><code>[홍길동]</code> 입력 시 한 칸에 알맞게 압축됩니다.</li>
            <li><code>[왼쪽/오른쪽]</code> 입력 시 두 열로 나뉩니다.</li>
            <li>글자가 많아지면 리본 밖으로 나가지 않도록 자동으로 여백에 딱 맞게(Squash) 조절됩니다.</li>
            <li><code>(주)</code> 등의 기호는 전각 최적화됩니다.</li>
          </ul>
        </div>

      </aside>

    </div>
  );
}
