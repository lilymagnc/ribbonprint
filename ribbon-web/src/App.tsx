import { useState, useEffect } from 'react';
import { 
  Printer, 
  PlusCircle, 
  Save, 
  FolderOpen, 
  Maximize2, 
  Minimize2, 
  RotateCw, 
  Ruler, 
  Scissors, 
  Settings2, 
  History,
  Type,
  MoveVertical
} from 'lucide-react';
import './index.css';

// 폰트 목록 (시스템 폰트 위주)
const FONTS = [
  { value: 'Gungsuh, serif', label: '궁서체 (Classic)' },
  { value: 'Batang, serif', label: '바탕체' },
  { value: 'Malgun Gothic, sans-serif', label: '맑은 고딕' },
  { value: 'Gulim, sans-serif', label: '굴림체' },
  { value: 'Nanum Myeongjo, serif', label: '나눔명조' },
];

const RIBBON_TYPES = [
  { id: 'standard', name: '3단 화환 (150x2000mm)', width: 150, length: 2000 },
  { id: 'oriental', name: '동양란 (45x450mm)', width: 45, length: 450 },
  { id: 'western', name: '서양란 (60x600mm)', width: 60, length: 600 },
  { id: 'custom', name: '직접 입력...', width: 100, length: 1000 },
];

/** 텍스트 파싱 및 정밀 제어 엔진 */
const parseLineContent = (rawLine: string, defaultSize: number, defaultOrientation: string) => {
  // 업계 표준인 '/' 기호를 줄바꿈으로 사용하기 위해 먼저 처리하는 경우도 있으나, 
  // 여기서는 라인 단위 파싱이므로 개별 라인 내의 마크업만 처리합니다.
  let text = rawLine.trim();
  let size = defaultSize;
  let orientation = defaultOrientation;

  let parsing = true;
  while(parsing) {
    if (text.startsWith('<') && text.endsWith('>')) {
      size *= 1.4;
      text = text.slice(1, -1).trim();
    } else if (text.startsWith('[') && text.endsWith(']')) {
      size *= 0.7;
      text = text.slice(1, -1).trim();
    } else if (text.startsWith('{') && text.endsWith('}')) {
      orientation = 'sideways';
      text = text.slice(1, -1).trim();
    } else {
      parsing = false;
    }
  }
  return { text, size, orientation };
};

const ControlGroup = ({ title, children, icon: Icon }: any) => (
  <div className="bg-white border-b border-gray-200 p-4">
    <div className="flex items-center gap-2 mb-3">
      {Icon && <Icon size={16} className="text-gray-500" />}
      <h3 className="text-xs font-bold text-gray-800 uppercase tracking-wider">{title}</h3>
    </div>
    <div className="space-y-3">
      {children}
    </div>
  </div>
);

const InputField = ({ label, children }: any) => (
  <div className="flex items-center gap-2">
    <label className="text-[11px] font-semibold text-gray-500 w-20 shrink-0">{label}</label>
    <div className="flex-1">
      {children}
    </div>
  </div>
);

function App() {
  // 전역 설정
  const [ribbonType, setRibbonType] = useState('standard');
  const [ribbonLength, setRibbonLength] = useState(2000);
  const [ribbonWidth, setRibbonWidth] = useState(150);
  const [marginTop, setMarginTop] = useState(150);
  const [marginBottom, setMarginBottom] = useState(150);
  const [printerName, setPrinterName] = useState('EPSON M105 Series');
  const [activeSide, setActiveSide] = useState<'left'|'right'>('left');

  // 좌측 리본 (경조사)
  const [leftText, setLeftText] = useState('축 발 전');
  const [leftFont, setLeftFont] = useState(FONTS[0].value);
  const [leftSize, setLeftSize] = useState(120);
  const [leftTracking, setLeftTracking] = useState(50);
  const [leftOrientation, setLeftOrientation] = useState('upright');
  const [leftPrint, setLeftPrint] = useState(true);

  // 우측 리본 (보내는이)
  const [rightText, setRightText] = useState('주식회사 ㅇㅇㅇ\\n대표이사 홍길동');
  const [rightFont, setRightFont] = useState(FONTS[2].value);
  const [rightSize, setRightSize] = useState(80);
  const [rightTracking, setRightTracking] = useState(15);
  const [rightOrientation, setRightOrientation] = useState('upright');
  const [rightPrint, setRightPrint] = useState(true);

  // 리본 타입 변경 시 자동 규격 설정
  useEffect(() => {
    const type = RIBBON_TYPES.find(t => t.id === ribbonType);
    if (type && type.id !== 'custom') {
      setRibbonWidth(type.width);
      setRibbonLength(type.length);
      if (type.id === 'oriental' || type.id === 'western') {
        setMarginTop(30);
        setMarginBottom(30);
        setLeftSize(40);
        setRightSize(30);
      } else {
        setMarginTop(150);
        setMarginBottom(150);
        setLeftSize(120);
        setRightSize(80);
      }
    }
  }, [ribbonType]);

  const handlePrint = async () => {
    const payload = {
      printer_name: printerName,
      paper_config: { length: ribbonLength, width: ribbonWidth, margin_top: marginTop, margin_bottom: marginBottom },
      print_left: leftPrint,
      print_right: rightPrint,
      configs: {
        '경조사': { text: leftText, font: leftFont, size: leftSize, tracking: leftTracking, orientation: leftOrientation },
        '보내는이': { text: rightText, font: rightFont, size: rightSize, tracking: rightTracking, orientation: rightOrientation },
      }
    };

    try {
      const res = await fetch('http://localhost:8000/api/print', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.status === 'success') alert('인쇄 명령이 전달되었습니다.');
      else alert('오류: ' + data.message);
    } catch (e) {
      alert('브릿지 서버 연결 실패: ' + e);
    }
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-[#f1f3f5] overflow-hidden select-none">
      {/* 1. 상단 전문 메뉴바 (Desktop App Style) */}
      <nav className="h-10 bg-[#343a40] flex items-center px-4 justify-between border-b border-black shrink-0">
        <div className="flex items-center gap-6">
          <div className="text-white font-bold text-sm tracking-tighter flex items-center gap-2 italic">
            <RotateCw size={14} className="text-blue-400" />
            RibbonMaker PRO 2026
          </div>
          <div className="flex gap-4 text-gray-300 text-[11px] font-medium">
             {['파일(F)', '편집(E)', '서식(T)', '보기(V)', '도움말(H)'].map(m => (
               <span key={m} className="hover:text-white cursor-pointer px-1">{m}</span>
             ))}
          </div>
        </div>
        <div className="flex items-center gap-3">
           <div className="text-[10px] text-gray-400">Ver 2.0.4 [Build 20260316]</div>
           <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
        </div>
      </nav>

      {/* 2. 툴바 (Ribbon Station Style) */}
      <div className="h-14 bg-gradient-to-b from-[#f8f9fa] to-[#e9ecef] border-b border-[#adb5bd] flex items-center px-4 gap-2 shrink-0 shadow-sm overflow-x-auto">
         <button className="flex flex-col items-center justify-center p-1 w-14 hover:bg-white border border-transparent hover:border-gray-300 rounded transition-all">
            <PlusCircle size={18} className="text-blue-600" />
            <span className="text-[10px] mt-1 font-bold">새 리본</span>
         </button>
         <button className="flex flex-col items-center justify-center p-1 w-14 hover:bg-white border border-transparent hover:border-gray-300 rounded transition-all">
            <FolderOpen size={18} className="text-orange-500" />
            <span className="text-[10px] mt-1 font-bold">열기</span>
         </button>
         <button className="flex flex-col items-center justify-center p-1 w-14 hover:bg-white border border-transparent hover:border-gray-300 rounded transition-all">
            <Save size={18} className="text-green-600" />
            <span className="text-[10px] mt-1 font-bold">저장</span>
         </button>
         <div className="w-px h-10 bg-gray-300 mx-1"></div>
         <button onClick={handlePrint} className="flex flex-col items-center justify-center p-1 w-16 bg-blue-50 border border-blue-200 hover:bg-blue-600 hover:text-white rounded transition-all group">
            <Printer size={18} className="text-blue-700 group-hover:text-white" />
            <span className="text-[10px] mt-1 font-bold">인쇄하기</span>
         </button>
         <div className="w-px h-10 bg-gray-300 mx-1"></div>
         <button className="flex flex-col items-center justify-center p-1 w-14 hover:bg-white border border-transparent hover:border-gray-300 rounded transition-all">
            <History size={18} className="text-gray-600" />
            <span className="text-[10px] mt-1 font-bold">이력관리</span>
         </button>
         <button className="flex flex-col items-center justify-center p-1 w-14 hover:bg-white border border-transparent hover:border-gray-300 rounded transition-all">
            <Settings2 size={18} className="text-gray-600" />
            <span className="text-[10px] mt-1 font-bold">설정</span>
         </button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* 3. 좌측: 파라미터 제어판 (전문가용 고밀도 UI) */}
        <aside className="w-[340px] bg-gray-100 border-r border-[#adb5bd] flex flex-col overflow-y-auto shrink-0 shadow-lg z-10">
          
          <ControlGroup title="리본 유형 및 프린터" icon={Scissors}>
            <InputField label="용지 종류">
              <select value={ribbonType} onChange={e => setRibbonType(e.target.value)} className="w-full p-1 border border-gray-300 rounded text-[11px] h-7 outline-none">
                {RIBBON_TYPES.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </InputField>
            <InputField label="프린터 연결">
              <select value={printerName} onChange={e => setPrinterName(e.target.value)} className="w-full p-1 border border-gray-300 rounded text-[11px] h-7 outline-none bg-blue-50">
                <option value="EPSON M105 Series">Epson M105 (Banner)</option>
                <option value="EPSON L1210">Epson L1210</option>
              </select>
            </InputField>
          </ControlGroup>

          <ControlGroup title="리본 규격 (mm)" icon={Ruler}>
            <div className="grid grid-cols-2 gap-x-4 gap-y-2">
              <InputField label="총 길이">
                <input type="number" value={ribbonLength} onChange={e => setRibbonLength(Number(e.target.value))} className="w-full p-1 border border-gray-300 rounded text-[11px] h-7 text-center" />
              </InputField>
              <InputField label="리본 폭">
                <input type="number" value={ribbonWidth} onChange={e => setRibbonWidth(Number(e.target.value))} className="w-full p-1 border border-gray-300 rounded text-[11px] h-7 text-center" />
              </InputField>
              <InputField label="상단 여백">
                <input type="number" value={marginTop} onChange={e => setMarginTop(Number(e.target.value))} className="w-full p-1 border border-gray-300 rounded text-[11px] h-7 text-center border-blue-200" />
              </InputField>
              <InputField label="하단 여백">
                <input type="number" value={marginBottom} onChange={e => setMarginBottom(Number(e.target.value))} className="w-full p-1 border border-gray-300 rounded text-[11px] h-7 text-center border-blue-200" />
              </InputField>
            </div>
          </ControlGroup>

          {/* 좌측 리본 제어 */}
          <ControlGroup title="좌측 리본 설정" icon={Type}>
            <div className="flex items-center justify-between mb-2">
               <div className="flex items-center gap-2">
                  <input type="checkbox" id="leftPrint" checked={leftPrint} onChange={e => setLeftPrint(e.target.checked)} className="accent-blue-600" />
                  <label htmlFor="leftPrint" className="text-[10px] font-bold text-blue-600 cursor-pointer">인쇄 포함</label>
               </div>
               <button 
                  onClick={() => setActiveSide('left')}
                  className={`px-2 py-0.5 text-[9px] rounded font-bold border transition-all ${activeSide === 'left' ? 'bg-blue-600 text-white border-blue-700' : 'bg-gray-200 text-gray-500 border-gray-300'}`}
               >
                  심볼 입력 대상
               </button>
            </div>
            <textarea 
               value={leftText.replace(/\\n/g, '\n')}
               onFocus={() => setActiveSide('left')}
               onChange={(e) => setLeftText(e.target.value.replace(/\n/g, '\\n'))}
               className="w-full h-20 p-2 border border-blue-300 rounded text-base font-bold outline-none focus:ring-1 focus:ring-blue-500 shadow-inner"
               placeholder="경조사 문구"
            />
            <div className="grid grid-cols-2 gap-2">
               <select value={leftFont} onChange={e => setLeftFont(e.target.value)} className="p-1 border border-gray-300 rounded text-[11px] h-7">
                  {FONTS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
               </select>
               <div className="flex items-center border border-gray-300 rounded overflow-hidden h-7">
                  <span className="bg-gray-100 text-[9px] px-1 text-gray-500 border-r border-gray-300 h-full flex items-center">Size</span>
                  <input type="number" value={leftSize} onChange={e => setLeftSize(Number(e.target.value))} className="w-full p-1 text-[11px] text-center" />
               </div>
            </div>
            <div className="flex items-center gap-2">
               <span className="text-[10px] text-gray-400 w-10">방향</span>
               <select value={leftOrientation} onChange={e => setLeftOrientation(e.target.value)} className="flex-1 p-1 border border-gray-300 rounded text-[10px] h-7 outline-none">
                  <option value="upright">세로쓰기 (정방향)</option>
                  <option value="sideways">가로쓰기 (회전)</option>
               </select>
            </div>
            <div className="flex items-center gap-2">
               <span className="text-[10px] text-gray-400 w-10">자간</span>
               <input type="range" min="-10" max="150" value={leftTracking} onChange={e => setLeftTracking(Number(e.target.value))} className="flex-1 accent-indigo-500" />
               <span className="text-[10px] font-mono w-6 text-right">{leftTracking}</span>
            </div>
          </ControlGroup>

          {/* 우측 리본 제어 */}
          <ControlGroup title="우측 리본 설정" icon={Type}>
            <div className="flex items-center justify-between mb-2">
               <div className="flex items-center gap-2">
                  <input type="checkbox" id="rightPrint" checked={rightPrint} onChange={e => setRightPrint(e.target.checked)} className="accent-blue-600" />
                  <label htmlFor="rightPrint" className="text-[10px] font-bold text-blue-600 cursor-pointer">인쇄 포함</label>
               </div>
               <button 
                  onClick={() => setActiveSide('right')}
                  className={`px-2 py-0.5 text-[9px] rounded font-bold border transition-all ${activeSide === 'right' ? 'bg-blue-600 text-white border-blue-700' : 'bg-gray-200 text-gray-500 border-gray-300'}`}
               >
                  심볼 입력 대상
               </button>
            </div>
            <textarea 
               value={rightText.replace(/\\n/g, '\n')}
               onFocus={() => setActiveSide('right')}
               onChange={(e) => setRightText(e.target.value.replace(/\n/g, '\\n'))}
               className="w-full h-20 p-2 border border-gray-300 rounded text-[13px] font-bold outline-none focus:ring-1 focus:ring-blue-500 shadow-inner"
               placeholder="보내는 이 문구"
            />
            <div className="grid grid-cols-2 gap-2">
               <select value={rightFont} onChange={e => setRightFont(e.target.value)} className="p-1 border border-gray-300 rounded text-[11px] h-7">
                  {FONTS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
               </select>
               <div className="flex items-center border border-gray-300 rounded overflow-hidden h-7">
                  <span className="bg-gray-100 text-[9px] px-1 text-gray-500 border-r border-gray-300 h-full flex items-center">Size</span>
                  <input type="number" value={rightSize} onChange={e => setRightSize(Number(e.target.value))} className="w-full p-1 text-[11px] text-center" />
               </div>
            </div>
            <div className="flex items-center gap-2">
               <span className="text-[10px] text-gray-400 w-10">방향</span>
               <select value={rightOrientation} onChange={e => setRightOrientation(e.target.value)} className="flex-1 p-1 border border-gray-300 rounded text-[10px] h-7 outline-none">
                  <option value="upright">세로쓰기 (정방향)</option>
                  <option value="sideways">가로쓰기 (회전)</option>
               </select>
            </div>
            <div className="flex items-center gap-2">
               <span className="text-[10px] text-gray-400 w-10">자간</span>
               <input type="range" min="-10" max="150" value={rightTracking} onChange={e => setRightTracking(Number(e.target.value))} className="flex-1 accent-indigo-500" />
               <span className="text-[10px] font-mono w-6 text-right">{rightTracking}</span>
            </div>
          </ControlGroup>

          {/* 특수 문자 및 심볼 뱅크 */}
          <ControlGroup title="심볼 패널 (Symbol Bank)">
             <div className="grid grid-cols-5 gap-1">
                {['★','(주)','(株)','🌹','🍃','卍','✝️','♥','🎗️','🚩'].map(s => (
                  <button key={s} onClick={() => activeSide === 'left' ? setLeftText(leftText + s) : setRightText(rightText + s)} className="h-8 border border-gray-300 bg-white hover:bg-blue-100 flex items-center justify-center text-xs rounded transition-all">{s}</button>
                ))}
             </div>
          </ControlGroup>
        </aside>

        {/* 4. 우측: 전문가용 고밀도 듀얼 리본 에디터 (Canvas Area) */}
        <main className="flex-1 bg-[#495057] p-10 overflow-auto flex justify-center items-start shadow-inner relative">
          
          <div className="flex gap-16 relative">
             {/* 왼쪽 눈금자 */}
             <div className="absolute -left-12 top-0 bottom-0 w-8 border-r border-gray-500 hidden md:flex flex-col select-none pointer-events-none opacity-40">
                {Array.from({ length: 21 }).map((_, i) => (
                  <div key={i} className="flex-1 border-t border-gray-400 relative">
                     <span className="absolute -top-2 left-0 text-[9px] text-gray-200">{(i * 100)}mm</span>
                  </div>
                ))}
             </div>

             {/* 왼쪽 리본 (경조사) */}
             <div className={`flex flex-col items-center gap-3 transition-opacity duration-300 ${!leftPrint ? 'opacity-30' : 'opacity-100'}`}>
                <div className="px-3 py-1 bg-black/40 text-white rounded-full text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
                   <MoveVertical size={12} /> 좌측 리본
                </div>
                <div className="w-[160px] h-[900px] bg-white shadow-[0_15px_60px_rgba(0,0,0,0.6)] relative overflow-hidden flex flex-col items-center group ribbon-texture">
                   {/* Satin Sheen Effect */}
                   <div className="absolute inset-0 silk-sheen opacity-10 pointer-events-none group-hover:translate-x-full transition-transform duration-1000"></div>
                   
                   <div className="flex-1 w-full flex justify-center" style={{ 
                      paddingTop: `${marginTop * 0.45}px`, 
                      paddingBottom: `${marginBottom * 0.45}px` 
                   }}>
                      {leftText.split(/[\\n/]/).map((rawLine, idx) => {
                         const { text, size, orientation } = parseLineContent(rawLine, leftSize, leftOrientation);
                         return (
                           <div key={idx} className="flex flex-col items-center mx-2 overflow-visible">
                              {text.split('').map((char, cIdx) => (
                                 <span key={cIdx} style={{ 
                                    fontFamily: leftFont, 
                                    fontSize: `${size}px`,
                                    marginBottom: `${leftTracking}px`,
                                    color: '#000',
                                    lineHeight: 1,
                                    transform: orientation === 'sideways' ? 'rotate(90deg)' : 'none',
                                    display: 'inline-block',
                                    fontWeight: 'bold'
                                 }}>{char}</span>
                              ))}
                           </div>
                         )
                      })}
                   </div>
                </div>
             </div>

             {/* 오른쪽 리본 (보내는이) */}
             <div className={`flex flex-col items-center gap-3 transition-opacity duration-300 ${!rightPrint ? 'opacity-30' : 'opacity-100'}`}>
                <div className="px-3 py-1 bg-black/40 text-white rounded-full text-[10px] font-bold uppercase tracking-widest flex items-center gap-2">
                   <MoveVertical size={12} /> 우측 리본
                </div>
                <div className="w-[160px] h-[900px] bg-[#fdfdfd] shadow-[0_15px_60px_rgba(0,0,0,0.6)] relative overflow-hidden flex flex-col items-center group ribbon-texture">
                   <div className="absolute inset-0 silk-sheen opacity-10 pointer-events-none group-hover:translate-x-full transition-transform duration-1000"></div>
                   
                   <div className="flex-1 w-full flex justify-center" style={{ 
                      paddingTop: `${marginTop * 0.45}px`, 
                      paddingBottom: `${marginBottom * 0.45}px` 
                   }}>
                      <div className="flex flex-row-reverse justify-center w-full">
                         {rightText.split(/[\\n/]/).map((rawLine, idx) => {
                            const { text, size, orientation } = parseLineContent(rawLine, rightSize, rightOrientation);
                            return (
                              <div key={idx} className="flex flex-col items-center mx-2 overflow-visible">
                                 {text.split('').map((char, cIdx) => (
                                    <span key={cIdx} style={{ 
                                       fontFamily: rightFont, 
                                       fontSize: `${size}px`,
                                       marginBottom: `${rightTracking}px`,
                                       color: '#000',
                                       lineHeight: 1,
                                       transform: orientation === 'sideways' ? 'rotate(90deg)' : 'none',
                                       display: 'inline-block',
                                       fontWeight: 'bold'
                                    }}>{char}</span>
                                 ))}
                              </div>
                            )
                         })}
                      </div>
                   </div>
                </div>
             </div>

             {/* 오른쪽 눈금자 */}
             <div className="absolute -right-12 top-0 bottom-0 w-8 border-l border-gray-500 hidden md:flex flex-col select-none pointer-events-none opacity-40">
                {Array.from({ length: 21 }).map((_, i) => (
                  <div key={i} className="flex-1 border-t border-gray-400 relative">
                     <span className="absolute -top-2 right-0 text-[9px] text-gray-200">{(i * 100)}mm</span>
                  </div>
                ))}
             </div>
          </div>

          {/* 뷰 조정 위젯 */}
          <div className="absolute bottom-6 right-6 flex gap-2">
             <button className="w-10 h-10 bg-white/10 hover:bg-white/20 border border-white/20 rounded flex items-center justify-center text-white backdrop-blur shadow-xl transition-all">
                <Minimize2 size={20} />
             </button>
             <button className="w-10 h-10 bg-white/10 hover:bg-white/20 border border-white/20 rounded flex items-center justify-center text-white backdrop-blur shadow-xl transition-all">
                <Maximize2 size={20} />
             </button>
          </div>
        </main>
      </div>

      {/* 5. 바닥글 (Status Bar) */}
      <footer className="h-7 bg-[#212529] border-t border-black flex items-center px-3 justify-between shrink-0">
         <div className="text-[10px] text-gray-400 flex items-center gap-4">
            <span>Ready</span>
            <div className="w-px h-3 bg-gray-700"></div>
            <span>Object: Hybrid Ribbon [Left: {leftPrint ? 'Enabled' : 'Disabled'} | Right: {rightPrint ? 'Enabled' : 'Disabled'}]</span>
            <div className="w-px h-3 bg-gray-700"></div>
            <span>Metric: {ribbonWidth}x{ribbonLength}mm</span>
         </div>
         <div className="text-[10px] text-gray-500 font-mono">
            CRC: 0xFD42 | UTF-8 | Win-Bridge 8000
         </div>
      </footer>
    </div>
  );
}

export default App;
