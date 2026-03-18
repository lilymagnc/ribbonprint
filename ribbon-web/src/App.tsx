import { useState, useEffect, useRef } from 'react';
import { 
  Printer, 
  Settings, 
  Ruler, 
  Type,
  Maximize2,
  Minimize2,
  RotateCw,
  Undo2
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

const PHRASE_CATEGORIES = [
  {
    name: '🎂 생일/회갑/칠순',
    phrases: [
      { text: '祝生日', desc: '축생일' }, { text: '祝生辰', desc: '축생신' }, { text: '祝華甲', desc: '축화갑(60)' },
      { text: '祝壽宴', desc: '축수연(60)' }, { text: '祝回甲', desc: '축회갑(60)' }, { text: '祝古稀', desc: '축고희(70)' },
      { text: '祝七旬', desc: '축칠순(70)' }, { text: '祝喜壽', desc: '축희수(77)' }, { text: '祝八旬', desc: '축팔순(80)' },
      { text: '祝傘壽', desc: '축산수(80)' }, { text: '祝米壽', desc: '축미수(88)' }, { text: '祝白壽', desc: '축백수(99)' },
      { text: 'Happy Birthday!', desc: '생일축하' }
    ]
  },
  {
    name: '🚀 승진/취임/영전',
    phrases: [
      { text: '祝昇進', desc: '축승진' }, { text: '祝榮轉', desc: '축영전' }, { text: '祝就任', desc: '축취임' },
      { text: '祝轉任', desc: '축전임' }, { text: '祝移任', desc: '축이임' }, { text: '祝遷任', desc: '축천임' },
      { text: '祝轉役', desc: '축전역' }, { text: '祝榮進', desc: '축영진' }, { text: '祝選任', desc: '축선임' },
      { text: '祝重任', desc: '축중임' }, { text: '祝連任', desc: '축연임' }, { text: 'Congratulations on your promotion', desc: '승진축하' }
    ]
  },
  {
    name: '🏢 개업/창립/이전',
    phrases: [
      { text: '祝發展', desc: '축발전' }, { text: '祝開業', desc: '축개업' }, { text: '祝盛業', desc: '축성업' },
      { text: '祝繁榮', desc: '축번영' }, { text: '祝創立', desc: '축창립' }, { text: '祝設立', desc: '축설립' },
      { text: '祝創設', desc: '축창설' }, { text: '祝創刊', desc: '축창간' }, { text: '祝移轉', desc: '축이전' },
      { text: '祝開院', desc: '축개원' }, { text: '祝開館', desc: '축개관' }, { text: '祝開場', desc: '축개장' },
      { text: '祝開店', desc: '축개점' }, { text: 'Congratulations on your new business', desc: '개업축하' }
    ]
  },
  {
    name: '💍 결혼/기념일',
    phrases: [
      { text: '祝約婚', desc: '축약혼' }, { text: '祝結婚', desc: '축결혼(男)' }, { text: '祝華婚', desc: '축화혼(女)' },
      { text: '祝成婚', desc: '축성혼' }, { text: '紙婚式', desc: '지혼식(1)' }, { text: '常婚式', desc: '상혼식(2)' },
      { text: '菓婚式', desc: '과혼식(3)' }, { text: '革婚式', desc: '혁혼식(4)' }, { text: '木婚式', desc: '목혼식(5)' },
      { text: '花婚式', desc: '화혼식(7)' }, { text: '祝錫婚式', desc: '축석혼(10)' }, { text: '痲婚式', desc: '마혼식(12)' },
      { text: '祝銅婚式', desc: '축동혼(15)' }, { text: '祝陶婚式', desc: '축도혼(20)' }, { text: '祝銀婚式', desc: '축은혼식(25)' },
      { text: '祝眞珠婚式', desc: '축진주혼식' }, { text: '祝珊瑚婚식', desc: '축산호혼식' }, { text: '祝錄玉婚式', desc: '축녹옥혼식' },
      { text: '祝紅玉婚式', desc: '축홍옥혼식' }, { text: '祝金婚式', desc: '축금혼식(50)' }, { text: '祝金剛婚式', desc: '축금강혼식(60)' },
      { text: 'A Happy Marriage', desc: '행복한결혼' }
    ]
  },
  {
    name: '🖤 죽음/애도',
    phrases: [
      { text: '謹弔', desc: '근조' }, { text: '追慕', desc: '추모' }, { text: '追悼', desc: '추도' },
      { text: '哀悼', desc: '애도' }, { text: '弔意', desc: '조의' }, { text: '尉靈', desc: '위령' },
      { text: '謹悼', desc: '근도' }, { text: '賻儀', desc: '부의' }, { text: '冥福', desc: '명복' },
      { text: '故人의 冥福을 빕니다', desc: '고인의 명복' }, { text: '삼가 故人의 冥福을 빕니다', desc: '삼가 명복' },
      { text: 'You have my condolences', desc: '애도' }, { text: 'Please accept my deepest condolences', desc: '깊은애도' }
    ]
  },
  {
    name: '🏢 준공/기공/개통',
    phrases: [
      { text: '祝起工', desc: '축기공' }, { text: '祝上樑', desc: '축상량' }, { text: '祝竣工', desc: '축준공' },
      { text: '祝開通', desc: '축개통' }, { text: '祝落成', desc: '축낙성' }
    ]
  },
  {
    name: '👶 출산/탄생',
    phrases: [
      { text: '祝順産', desc: '축순산' }, { text: '祝出産', desc: '축출산' }, { text: '祝誕生', desc: '축탄생' },
      { text: '祝得男', desc: '축득남' }, { text: '祝得女', desc: '축득녀' }, { text: '祝公主誕生', desc: '축공주탄생' },
      { text: '祝王子誕生', desc: '축왕자탄생' }, { text: 'Congratulations on your new baby', desc: '출산축하' }
    ]
  },
  {
    name: '📚 창간/출판',
    phrases: [
      { text: '祝創刊', desc: '축창간' }, { text: '祝發刊', desc: '축발간' }, { text: '祝出版紀念', desc: '축출판기념' },
      { text: '出版紀念會', desc: '출판기념회' }
    ]
  },
  {
    name: '🎨 전시/연주',
    phrases: [
      { text: '祝展覽會', desc: '축전람회' }, { text: '祝展示會', desc: '축전시회' }, { text: '祝品評會', desc: '축품평회' },
      { text: '祝博覽會', desc: '축박람회' }, { text: '祝蓮奏會', desc: '축연주회' }, { text: '祝獨奏會', desc: '축독주회' },
      { text: '祝個人展', desc: '축개인전' }
    ]
  },
  {
    name: '🎓 입학/졸업/합격',
    phrases: [
      { text: '祝入學', desc: '축입학' }, { text: '祝卒業', desc: '축졸업' }, { text: '祝合格', desc: '축합격' },
      { text: '祝博士學位記授與', desc: '축박사학위' }, { text: '祝開校', desc: '축개교' }, { text: '頌功', desc: '송공' },
      { text: '祝停年退任', desc: '축정년퇴임' }
    ]
  },
  {
    name: '🏆 우승/당선',
    phrases: [
      { text: '祝優勝', desc: '축우승' }, { text: '祝入選', desc: '축입선' }, { text: '祝必勝', desc: '축필승' },
      { text: '祝健勝', desc: '축건승' }, { text: '祝當選', desc: '축당선' }, { text: '祝被選', desc: '축피선' }
    ]
  },
  {
    name: '⛪ 교회/종교',
    phrases: [
      { text: '獻堂', desc: '헌당' }, { text: '祝長老長立', desc: '축장로장립' }, { text: '牧師按手', desc: '목사안수' },
      { text: '靈名祝日', desc: '영명축일' }, { text: '祝勸士就任', desc: '축권사취임' }, { text: '祝牧師委任', desc: '축목사위임' }
    ]
  },
  {
    name: '🎍 연말연시/시즌',
    phrases: [
      { text: '謹賀新年', desc: '근하신년' }, { text: '送舊迎新', desc: '송구영신' }, { text: '仲秋佳節', desc: '중추가절' },
      { text: 'Happy New Year!', desc: '새해복' }, { text: 'Merry Christmas!', desc: '메리크리스마스' }
    ]
  }
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
      // default all to standing (false), rotate only if user clicked (id exists in rotatedIds)
      const isRotated = rotatedIds.has(id);
      
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
  const [phraseCategory, setPhraseCategory] = useState(0);

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

  const handleRotateAll = (side: 'left'|'right') => {
    const text = side === 'left' ? leftText : rightText;
    const lines = text.split('\n').filter(l => l.trim() !== '');
    const newRotated = new Set<string>();
    lines.forEach((line, lIdx) => {
      // Must match RibbonCanvas baseId pattern: 'L' + index
      const nodes = parseRibbonLine(line, `L${lIdx}`, new Set());
      nodes.forEach(n => {
        if (n.type === 'char') newRotated.add(n.id);
      });
    });
    if (side === 'left') setLeftRotated(newRotated);
    else setRightRotated(newRotated);
  };

  const handleResetRotation = (side: 'left'|'right') => {
    if (side === 'left') setLeftRotated(new Set());
    else setRightRotated(new Set());
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
            <div className="flex items-center gap-1">
              <button 
                title="전체 90도 회전"
                onClick={() => handleRotateAll('left')} 
                className="hover:bg-slate-700 p-1 rounded text-slate-400 hover:text-white transition-colors"
              >
                <RotateCw size={14} />
              </button>
              <button 
                title="회전 초기화"
                onClick={() => handleResetRotation('left')} 
                className="hover:bg-slate-700 p-1 rounded text-slate-400 hover:text-white transition-colors"
              >
                <Undo2 size={14} />
              </button>
              <button 
                onClick={() => setActiveSide('left')}
                className={cn("text-[10px] px-2 py-0.5 rounded font-bold transition-all ml-1", activeSide === 'left' ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-400")}
              >ACTIVE</button>
            </div>
          </div>
          <input 
            type="text"
            value={leftText} 
            onChange={e => setLeftText(e.target.value)}
            onFocus={() => setActiveSide('left')}
            className={cn("w-full p-2 rounded-lg text-sm leading-tight focus:ring-2 bg-slate-800 border-slate-700 text-white outline-none", leftFont)}
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
            <div className="flex items-center gap-1">
              <button 
                title="전체 90도 회전"
                onClick={() => handleRotateAll('right')} 
                className="hover:bg-slate-700 p-1 rounded text-slate-400 hover:text-white transition-colors"
              >
                <RotateCw size={14} />
              </button>
              <button 
                title="회전 초기화"
                onClick={() => handleResetRotation('right')} 
                className="hover:bg-slate-700 p-1 rounded text-slate-400 hover:text-white transition-colors"
              >
                <Undo2 size={14} />
              </button>
              <button 
                onClick={() => setActiveSide('right')}
                className={cn("text-[10px] px-2 py-0.5 rounded font-bold transition-all ml-1", activeSide === 'right' ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-400")}
              >ACTIVE</button>
            </div>
          </div>
          <input 
            type="text"
            value={rightText} 
            onChange={e => setRightText(e.target.value)}
            onFocus={() => setActiveSide('right')}
            className={cn("w-full p-2 rounded-lg text-sm leading-tight focus:ring-2 bg-slate-800 border-slate-700 text-white outline-none", rightFont)}
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
          <div className="flex items-center justify-between border-b border-slate-700 pb-2 mb-3">
             <h2 className="text-sm font-bold text-slate-300">자주 쓰는 상용구</h2>
             <select 
               value={phraseCategory} 
               onChange={e => setPhraseCategory(Number(e.target.value))}
               className="bg-slate-800 text-[10px] border-none rounded px-2 py-1 outline-none focus:ring-1 ring-blue-500 text-slate-300"
             >
               {PHRASE_CATEGORIES.map((cat, idx) => <option key={idx} value={idx}>{cat.name.split(' ')[1] || cat.name}</option>)}
             </select>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {PHRASE_CATEGORIES[phraseCategory].phrases.map((item, idx) => (
               <button 
                 key={idx} 
                 onClick={() => {
                   if (activeSide === 'left') setLeftText(item.text);
                   else setRightText(item.text);
                 }}
                 className="group bg-slate-800 hover:bg-blue-900/30 border border-slate-700 hover:border-blue-500 rounded p-2 transition-all flex flex-col items-center justify-center min-h-[50px]"
               >
                 <span className="text-[12px] font-bold text-slate-200 mb-0.5 leading-tight">{item.text}</span>
                 <span className="text-[9px] text-slate-500 group-hover:text-blue-300">{item.desc}</span>
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
