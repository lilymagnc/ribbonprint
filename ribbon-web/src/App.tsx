import { useState } from 'react';
import './index.css';

// 폰트 목록
const FONTS = [
  { value: 'Gungsuh, serif', label: '궁서체' },
  { value: 'Batang, serif', label: '바탕체' },
  { value: 'Malgun Gothic, sans-serif', label: '맑은 고딕' },
  { value: 'Gulim, sans-serif', label: '굴림체' },
];

/** 텍스트 라인의 특수 마크업 괄호를 파싱해 개별 폰트 스타일을 반환합니다. */
const parseLineContent = (rawLine: string, defaultSize: number, defaultOrientation: string) => {
  let text = rawLine.trim();
  let size = defaultSize;
  let orientation = defaultOrientation;

  let parsing = true;
  while(parsing) {
    if (text.startsWith('<') && text.endsWith('>')) {
      size *= 1.4; // 확대
      text = text.slice(1, -1).trim();
    } else if (text.startsWith('[') && text.endsWith(']')) {
      size *= 0.7; // 축소
      text = text.slice(1, -1).trim();
    } else if (text.startsWith('{') && text.endsWith('}')) {
      orientation = 'sideways'; // 세로쓰기 중 부분 가로쓰기
      text = text.slice(1, -1).trim();
    } else {
      parsing = false;
    }
  }
  return { text, size, orientation };
};

function App() {
  const [activeTab, setActiveTab] = useState<'left'|'right'>('left');
  
  // 상태 관리: 좌측 리본(경조사)
  const [leftText, setLeftText] = useState('축 발 전');
  const [leftFont, setLeftFont] = useState(FONTS[0].value);
  const [leftSize, setLeftSize] = useState(120);
  const [leftTracking, setLeftTracking] = useState(50); // 자간

  // 상태 관리: 우측 리본(보내는 분)
  const [rightText, setRightText] = useState('주식회사 ㅇㅇㅇ\\n대표이사 홍길동');
  const [rightFont, setRightFont] = useState(FONTS[2].value);
  const [rightSize, setRightSize] = useState(80);
  const [rightTracking, setRightTracking] = useState(10);

  // 세로쓰기 내 글자 회전 (정방향=upright, 누운방향=sideways)
  const [leftOrientation, setLeftOrientation] = useState('upright');
  const [rightOrientation, setRightOrientation] = useState('upright');

  // 리본 물리 규격 설정 (mm 단위)
  const [ribbonLength, setRibbonLength] = useState(2000); // 2m
  const [ribbonWidth, setRibbonWidth] = useState(150);    // 15cm
  const [marginTop, setMarginTop] = useState(100);        // 상단 여백
  const [marginBottom, setMarginBottom] = useState(100);  // 하단 여백
  const textSpaceLength = ribbonLength - marginTop - marginBottom;

  const [printerName, setPrinterName] = useState('EPSON M105 Series');

  const handlePrint = async () => {
    const payload = {
      printer_name: printerName,
      paper_config: { length: ribbonLength, width: ribbonWidth, margin_top: marginTop, margin_bottom: marginBottom },
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
      
      if (data.status === 'success') {
         alert('프린터로 인쇄 명령을 전송했습니다!');
      } else {
         alert('인쇄 실패: ' + data.message);
      }
    } catch (error) {
       console.error(error);
       alert('브릿지 서버(http://localhost:8000)를 찾을 수 없습니다.');
    }
  };

  const insertSymbol = (symbol: string) => {
    if (activeTab === 'left') {
      setLeftText(leftText + symbol);
    } else {
       setRightText(rightText + symbol);
    }
  };

  return (
    <div className="flex h-screen bg-[#e8eaed] font-sans text-neutral-800 flex-col overflow-hidden">
      {/* 최상단 툴바 (데스크톱 앱 스타일) */}
      <header className="bg-gradient-to-b from-[#f8f9fa] to-[#e9ecef] border-b border-[#ced4da] h-14 flex items-center px-4 justify-between shadow-sm z-20 shrink-0">
        <div className="flex items-center gap-4">
          <div className="font-bold text-[#495057] text-lg tracking-tight flex items-center gap-2">
            <span className="text-blue-600 bg-blue-100 px-2 py-0.5 rounded text-sm">PRO</span>
            화환 리본 프린터 시스템
          </div>
          <div className="h-6 w-px bg-gray-300 mx-2"></div>
          <div className="flex gap-1">
             <button className="px-3 py-1.5 text-sm outline-none border border-transparent hover:border-gray-300 hover:bg-white rounded transition-colors text-gray-700">새 문서</button>
             <button className="px-3 py-1.5 text-sm outline-none border border-transparent hover:border-gray-300 hover:bg-white rounded transition-colors text-gray-700">불러오기</button>
             <button className="px-3 py-1.5 text-sm outline-none border border-transparent hover:border-gray-300 hover:bg-white rounded transition-colors text-gray-700">저장</button>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <select 
            value={printerName}
            onChange={(e) => setPrinterName(e.target.value)}
            className="text-sm p-1.5 border border-gray-300 rounded bg-white w-48 shadow-sm"
          >
             <option value="EPSON M105 Series">COM1 : EPSON M105</option>
             <option value="EPSON L1210">USB : EPSON L1210</option>
          </select>
          <button 
             onClick={handlePrint}
             className="px-6 py-1.5 bg-gradient-to-b from-blue-500 to-blue-700 hover:from-blue-600 hover:to-blue-800 text-white font-bold text-sm rounded shadow border border-blue-800 transition-all flex items-center gap-2"
          >
            🖨️ 인쇄 (Print)
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* 좌측: 컨트롤 패널 (입력기) */}
        <aside className="w-[380px] bg-[#f1f3f5] border-r border-[#ced4da] flex flex-col z-10 shrink-0 shadow-[2px_0_5px_rgba(0,0,0,0.05)]">
           {/* 탭버튼 */}
           <div className="flex border-b border-gray-300 bg-[#e9ecef]">
              <button 
                onClick={() => setActiveTab('left')}
                className={`flex-1 py-2.5 text-sm font-bold border-r border-gray-300 transition-colors ${activeTab === 'left' ? 'bg-white text-blue-700 border-b-white transform translate-y-[1px]' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                좌측 리본 (경조사)
              </button>
              <button 
                onClick={() => setActiveTab('right')}
                className={`flex-1 py-2.5 text-sm font-bold transition-colors ${activeTab === 'right' ? 'bg-white text-blue-700 border-b-white transform translate-y-[1px]' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                우측 리본 (보내는분)
              </button>
           </div>

           <div className="p-4 flex-1 overflow-y-auto bg-white flex flex-col gap-5">
              
              {/* 공통: 문구 입력 */}
              <div className="flex flex-col gap-2">
                 <label className="text-xs font-bold text-gray-700 uppercase flex justify-between">
                    텍스트 입력
                    <span className="font-normal text-gray-400">Enter로 줄바꿈</span>
                 </label>
                 <textarea 
                   value={activeTab === 'left' ? leftText.replace(/\\n/g, '\n') : rightText.replace(/\\n/g, '\n')}
                   onChange={(e) => {
                      const val = e.target.value.replace(/\n/g, '\\n');
                      if (activeTab === 'left') setLeftText(val);
                      else setRightText(val);
                   }}
                   className="w-full h-32 p-3 border border-gray-300 rounded shadow-inner text-lg focus:outline-none focus:border-blue-500 font-medium"
                   placeholder={activeTab === 'left' ? "축 발 전" : "보내는 분 명칭"}
                 />
              </div>

              {/* 기호 삽입 툴바 */}
              <div className="bg-gray-50 p-2 border border-gray-200 rounded">
                <div className="text-[11px] font-bold text-gray-500 mb-1.5">특수기호 삽입</div>
                <div className="flex flex-wrap gap-1">
                   {['★','☆','♥','♡','🌷','🌸','🏵️','🎗️','■','▲','[',']'].map(sym => (
                      <button key={sym} onClick={() => insertSymbol(sym)} className="w-8 h-8 flex items-center justify-center bg-white border border-gray-300 rounded hover:bg-blue-50 hover:border-blue-300 text-sm">{sym}</button>
                   ))}
                </div>
              </div>

               {/* 리본 규격(mm) 설정 박스 (공통형) */}
               <div className="bg-white border border-gray-200 rounded p-3 flex flex-col gap-4 shadow-sm relative overflow-hidden">
                 <div className="text-[11px] font-bold text-gray-500 uppercase border-b border-gray-100 pb-1 flex justify-between">
                   리본 규격 제어 (mm)
                   <span className="text-[10px] text-gray-400 bg-gray-100 px-1 rounded">고급설정</span>
                 </div>
                 
                 <div className="flex items-center gap-2">
                    <label className="text-sm font-medium w-16 text-gray-700">총 길이</label>
                    <input type="number" value={ribbonLength} onChange={e => setRibbonLength(Number(e.target.value))} className="w-16 p-1 border border-gray-300 rounded text-sm text-center" />
                    <span className="text-xs text-gray-400">mm</span>
                    <div className="w-px h-4 bg-gray-300 mx-1"></div>
                    <label className="text-sm font-medium w-8 text-gray-700">폭</label>
                    <select value={ribbonWidth} onChange={e => setRibbonWidth(Number(e.target.value))} className="flex-1 p-1 border border-gray-300 rounded text-sm outline-none">
                       <option value={150}>150mm</option>
                       <option value={100}>100mm</option>
                    </select>
                 </div>

                 <div className="flex gap-4">
                    <div className="flex-1 flex flex-col gap-1">
                       <label className="text-[10px] text-gray-500 text-center">상단 여백</label>
                       <div className="flex items-center border border-gray-300 rounded overflow-hidden">
                          <input type="number" value={marginTop} onChange={e => setMarginTop(Number(e.target.value))} className="w-full p-1 text-sm text-center outline-none" />
                          <div className="bg-gray-100 text-xs px-1 text-gray-400 border-l border-gray-200">mm</div>
                       </div>
                    </div>
                    <div className="flex-1 flex flex-col gap-1">
                       <label className="text-[10px] text-gray-500 text-center">글자 영역</label>
                       <div className="flex items-center border border-gray-300 rounded overflow-hidden bg-gray-50">
                          <input type="number" value={textSpaceLength} readOnly className="w-full p-1 text-sm text-center outline-none bg-transparent text-gray-500" />
                          <div className="bg-gray-200 text-xs px-1 text-gray-500 border-l border-gray-300">mm</div>
                       </div>
                    </div>
                    <div className="flex-1 flex flex-col gap-1">
                       <label className="text-[10px] text-gray-500 text-center">하단 여백</label>
                       <div className="flex items-center border border-gray-300 rounded overflow-hidden">
                          <input type="number" value={marginBottom} onChange={e => setMarginBottom(Number(e.target.value))} className="w-full p-1 text-sm text-center outline-none" />
                          <div className="bg-gray-100 text-xs px-1 text-gray-400 border-l border-gray-200">mm</div>
                       </div>
                    </div>
                 </div>
               </div>

               {/* 폰트/스타일 설정 폼 박스 */}
               <div className="bg-gray-50 border border-gray-200 rounded p-3 flex flex-col gap-4 shadow-sm">
                 <div className="text-[11px] font-bold text-gray-500 uppercase border-b border-gray-200 pb-1 flex justify-between">
                     글꼴 속성 제어
                 </div>
                 <div className="text-[10px] text-blue-600 bg-blue-50 p-1.5 rounded -mt-2 leading-tight">
                    💡 빠른 포맷 기능: 텍스트를 기호로 감싸보세요.<br/>
                    <b>&lt;문구&gt;</b>: 확대 / <b>[문구]</b>: 축소 / <b>&#123;문구&#125;</b>: 90도 회전
                 </div>
                 
                 <div className="flex items-center gap-3">
                    <label className="text-sm font-medium w-12 text-gray-700">글꼴</label>
                    <select 
                        value={activeTab === 'left' ? leftFont : rightFont}
                        onChange={(e) => activeTab === 'left' ? setLeftFont(e.target.value) : setRightFont(e.target.value)}
                        className="flex-1 p-1.5 border border-gray-300 rounded text-sm outline-none focus:border-blue-500 shadow-inner"
                    >
                       {FONTS.map(f => <option key={f.value} value={f.value}>{f.label}</option>)}
                    </select>
                 </div>

                 <div className="flex items-center gap-3">
                    <label className="text-sm font-medium w-12 text-gray-700">크기</label>
                    <input 
                      type="number" 
                      value={activeTab === 'left' ? leftSize : rightSize}
                      onChange={(e) => activeTab === 'left' ? setLeftSize(Number(e.target.value)) : setRightSize(Number(e.target.value))}
                      className="w-20 p-1.5 border border-gray-300 rounded text-sm outline-none focus:border-blue-500 shadow-inner"
                    />
                    <span className="text-xs text-gray-500 text-left flex-1">pt</span>
                 </div>

                 <div className="flex items-center gap-3 w-full">
                    <label className="text-sm font-medium w-12 text-gray-700">자간</label>
                    <input 
                        type="range" 
                        min="-20" max="200" 
                        value={activeTab === 'left' ? leftTracking : rightTracking}
                        onChange={(e) => activeTab === 'left' ? setLeftTracking(Number(e.target.value)) : setRightTracking(Number(e.target.value))}
                        className="flex-1 accent-blue-600"
                    />
                    <span className="w-8 text-right text-xs bg-white border border-gray-200 px-1 py-0.5 rounded shadow-sm">{activeTab === 'left' ? leftTracking : rightTracking}</span>
                 </div>

                 <div className="flex items-center gap-3">
                    <label className="text-sm font-medium w-12 text-gray-700">방향</label>
                    <select 
                        value={activeTab === 'left' ? leftOrientation : rightOrientation}
                        onChange={(e) => activeTab === 'left' ? setLeftOrientation(e.target.value) : setRightOrientation(e.target.value)}
                        className="flex-1 p-1.5 border border-gray-300 rounded text-sm outline-none focus:border-blue-500"
                    >
                       <option value="upright">세로쓰기 (정방향)</option>
                       <option value="sideways">가로쓰기 (90도 회전)</option>
                    </select>
                 </div>
              </div>
              
              {/* 상용구 영역 */}
              <div className="flex flex-col gap-2 mt-auto">
                 <label className="text-xs font-bold text-gray-700 uppercase">상용 문구 (더블클릭)</label>
                 <div className="h-32 border border-gray-300 rounded bg-white overflow-y-auto">
                    {['축 발 전', '축 개 업', '근 조', '삼가 고인의 명복을 빕니다', '축 결 혼', '축 화 환'].map(phrase => (
                       <div key={phrase} 
                            onDoubleClick={() => activeTab === 'left' ? setLeftText(phrase) : setRightText(phrase)}
                            className="px-3 py-1.5 text-sm cursor-pointer hover:bg-blue-50 border-b border-gray-100 last:border-0"
                       >
                         {phrase}
                       </div>
                    ))}
                 </div>
              </div>

           </div>
        </aside>

        {/* 3. 우측: 캔버스 (리본 미리보기) */}
        <div className="flex-1 bg-[#8fa4a6] overflow-y-auto relative p-8 shadow-inner flex" style={{ backgroundImage: "repeating-linear-gradient(45deg, rgba(255,255,255,0.03) 0, rgba(255,255,255,0.03) 2px, transparent 2px, transparent 8px)" }}>
           
           {/* 가상 눈금자 (Ruler) */}
           <div className="w-8 h-[800px] border-r border-[#698083] flex flex-col items-end pr-2 py-16 mr-8 sticky left-0 z-10 shrink-0 opacity-70">
              {Array.from({ length: 17 }).map((_, i) => (
                 <div key={i} className="flex-1 w-full flex flex-col justify-start items-end border-t border-[#465a5d]/30 relative">
                    <span className="absolute -top-2 -left-2 text-[10px] text-black/40 font-bold">{i * 10}</span>
                    <div className="w-2 h-px bg-[#465a5d]/30 mt-auto"></div>
                    <div className="w-1 h-px bg-[#465a5d]/30 mt-auto"></div>
                    <div className="w-3 h-px bg-[#465a5d]/30 mt-auto"></div>
                 </div>
              ))}
           </div>
           
           <div className="w-full max-w-2xl flex justify-between px-10 relative">
              {/* 리본 1: 좌측(경조사) */}
              <div className="flex flex-col items-center gap-4">
                 <div className="font-bold text-white/80 text-sm tracking-widest bg-black/20 px-4 py-1.5 rounded-full">좌측 리본 (경조사)</div>
                 
                 {/* 세로 리본 컨테이너 */}
                 <div className="relative w-[140px] h-[800px] bg-gradient-to-b from-[#ffe4e1] to-[#fff0f5] shadow-[0_10px_30px_rgba(0,0,0,0.3)] flex flex-col items-center overflow-hidden border border-pink-100">
                    <div className="absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-black/20 to-transparent"></div>
                    <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.7%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22/%3E%3C/svg%3E')"}}></div>
                    
                    <div className="flex-1 w-full flex justify-center" style={{ 
                       paddingTop: `${marginTop * 0.4}px`, 
                       paddingBottom: `${marginBottom * 0.4}px` 
                    }}>
                       {leftText.split('\\n').map((rawLine, idx) => {
                           const { text, size, orientation } = parseLineContent(rawLine, leftSize, leftOrientation);
                           return (
                             <div key={idx} className="flex flex-col items-center mx-2 overflow-visible">
                                {text.split('').map((char, cIdx) => (
                                   <span key={cIdx} style={{ 
                                      fontFamily: leftFont, 
                                      fontSize: `${size}px`,
                                      marginBottom: `${leftTracking}px`,
                                      color: '#111',
                                      textShadow: '1px 1px 0px rgba(255,255,255,0.8)',
                                      lineHeight: 1,
                                      transform: orientation === 'sideways' ? 'rotate(90deg)' : 'none',
                                      display: 'inline-block'
                                   }}>{char}</span>
                                ))}
                             </div>
                           )
                       })}
                    </div>
                 </div>
              </div>

              {/* 리본 2: 우측(보내는 분) */}
              <div className="flex flex-col items-center gap-4">
                 <div className="font-bold text-white/80 text-sm tracking-widest bg-black/20 px-4 py-1.5 rounded-full">우측 리본 (보내는분)</div>
                 
                 {/* 세로 리본 컨테이너 */}
                 <div className="relative w-[140px] h-[800px] bg-gradient-to-b from-[#fdfbf7] to-[#f8f9fa] shadow-[0_10px_30px_rgba(0,0,0,0.3)] flex flex-col items-center overflow-hidden border border-gray-200">
                    <div className="absolute inset-x-0 top-0 h-8 bg-gradient-to-b from-black/20 to-transparent"></div>
                    <div className="absolute inset-0 opacity-[0.04] pointer-events-none" style={{ backgroundImage: "url('data:image/svg+xml,%3Csvg viewBox=%220 0 200 200%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.7%22 numOctaves=%223%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22/%3E%3C/svg%3E')"}}></div>
                    
                    <div className="flex-1 w-full flex justify-center" style={{ 
                       paddingTop: `${marginTop * 0.4}px`, 
                       paddingBottom: `${marginBottom * 0.4}px` 
                    }}>
                       {/* 보내는분도 세로쓰기를 기본으로 유지 */}
                       <div className="flex flex-row-reverse justify-center w-full">
                         {rightText.split('\\n').map((rawLine, idx) => {
                             const { text, size, orientation } = parseLineContent(rawLine, rightSize, rightOrientation);
                             return (
                               <div key={idx} className="flex flex-col items-center mx-2 overflow-visible">
                                  {text.split('').map((char, cIdx) => (
                                     <span key={cIdx} style={{ 
                                        fontFamily: rightFont, 
                                        fontSize: `${size}px`,
                                        marginBottom: `${rightTracking}px`,
                                        color: '#111',
                                        lineHeight: 1,
                                        transform: orientation === 'sideways' ? 'rotate(90deg)' : 'none',
                                        display: 'inline-block'
                                     }}>{char}</span>
                                  ))}
                               </div>
                             )
                         })}
                       </div>
                    </div>
                 </div>
              </div>

           </div>
        </div>
      </div>
    </div>
  );
}

export default App;
