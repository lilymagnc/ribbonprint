"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Download, Printer, Undo2, Redo2, Save, FolderOpen, HelpCircle, PlusCircle, ChevronLeft, ChevronRight, Settings } from "lucide-react";


type Side = "left" | "right";

interface FontFace {
    family: string;
    status: string;
}

function mmToPx(mm: number): number {
	return Math.round(mm * 3.7795275591);
}

interface RibbonTextSettings {
	label: string;
	fontFamily: string;
	fontSizePx: number;
	isBold: boolean;
	isItalic: boolean;
	color: string;
	content: string;
	charSpacingMm: number;
	topMarginMm: number;
	bottomMarginMm: number;
	autoFit: boolean;
	sidePaddingMm: number;
	// Font fallbacks per script (used as chained family list)
	koreanFont?: string;
	cjkFont?: string;
	latinFont?: string;
    verticalDirection?: "top-down" | "bottom-up";
    horizontalAlign?: "left" | "center" | "right";
    scaleX: number; // horizontal glyph scale multiplier (1 = 100%)
    scaleY: number; // vertical glyph scale multiplier (pre-fill adjustment)
    applyBracketScale?: boolean; // if true, content inside [ ] rendered smaller
    bracketScale?: number; // 0~1, inner text scale
    bracketSpacerFactor?: number; // 0~1, visual gap for '[' and ']' themselves
}

export default function Home() {
	// Global ribbon sizing (shared)
	const [ribbonWidthMm, setRibbonWidthMm] = useState<number>(38);
	const [ribbonLengthMm, setRibbonLengthMm] = useState<number>(400);
	const [backgroundColor, setBackgroundColor] = useState<string>("#ffffff");
	const [scale, setScale] = useState<number>(0.6);
	const [applyBoth, setApplyBoth] = useState<boolean>(true);

    // UI string states for scale inputs to avoid flicker while typing
    const [leftScaleXStr, setLeftScaleXStr] = useState<string>("100");
    const [leftScaleYStr, setLeftScaleYStr] = useState<string>("100");
    const [rightScaleXStr, setRightScaleXStr] = useState<string>("100");
    const [rightScaleYStr, setRightScaleYStr] = useState<string>("100");

	// Left/Right text settings
	const [leftSettings, setLeftSettings] = useState<RibbonTextSettings>({
		label: "경조사",
		fontFamily: "Arial",
		fontSizePx: 28,
		isBold: false,
		isItalic: false,
		color: "#111111",
		content: "경조사어 리본",
		charSpacingMm: 5,
		topMarginMm: 20,
		bottomMarginMm: 20,
		autoFit: true,
		sidePaddingMm: 2,
		koreanFont: "ChosunGs",
		cjkFont: "ChosunGs",
		latinFont: "Arial",
        verticalDirection: "top-down",
        horizontalAlign: "center",
        scaleX: 1,
        scaleY: 1,
        applyBracketScale: false,
        bracketScale: 0.5,
        bracketSpacerFactor: 0.5,
	});
	const [rightSettings, setRightSettings] = useState<RibbonTextSettings>({
		label: "보내는이",
		fontFamily: "Arial",
		fontSizePx: 28,
		isBold: false,
		isItalic: false,
		color: "#111111",
		content: "보내는이\n[회사명]",
		charSpacingMm: 5,
		topMarginMm: 20,
		bottomMarginMm: 20,
		autoFit: true,
		sidePaddingMm: 2,
		koreanFont: "ChosunGs",
		cjkFont: "ChosunGs",
		latinFont: "Arial",
        verticalDirection: "top-down",
        horizontalAlign: "center",
        scaleX: 1,
        scaleY: 1,
		applyBracketScale: true,
        bracketScale: 0.5,
        bracketSpacerFactor: 0.5,
	});

	// Derived pixels
	const ribbonWidthPx = useMemo(() => mmToPx(ribbonWidthMm), [ribbonWidthMm]);
    const ribbonLengthPx = useMemo(() => mmToPx(ribbonLengthMm), [ribbonLengthMm]);
    const totalCanvasWidthPx = useMemo(() => 34 + ribbonWidthPx + 34, [ribbonWidthPx]); // rulerPx * 2 + ribbonWidthPx
    const gapPx = 40; // Tailwind gap-10 ≈ 40px
    const contentWidthPx = useMemo(() => totalCanvasWidthPx * 2 + gapPx, [totalCanvasWidthPx]);
    const previewContainerRef = useRef<HTMLDivElement | null>(null);
    const [containerWidth, setContainerWidth] = useState<number>(0);

    const [fitBoth, setFitBoth] = useState<boolean>(true);
    useEffect(() => {
        const el = previewContainerRef.current;
        if (!el) return;
        const ro = new ResizeObserver(entries => {
            for (const e of entries) {
                const cr = e.contentRect;
                setContainerWidth(Math.max(0, cr.width - 16));
            }
        });
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    // Observe left settings panel height to sync preview height
    useEffect(() => {
        const el = leftPanelRef.current;
        if (!el) return;
        const ro = new ResizeObserver(entries => {
            for (const e of entries) {
                const cr = e.contentRect;
                setLeftPanelHeight(Math.round(cr.height));
            }
        });
        ro.observe(el);
        // initial read
        setLeftPanelHeight(Math.round(el.getBoundingClientRect().height));
        return () => ro.disconnect();
    }, []);
    const computedFitScale = useMemo(() => {
        if (containerWidth <= 0) return scale;
        const sW = containerWidth / Math.max(1, contentWidthPx);
        // 폭 기준으로만 자동 맞춤. 세로는 스크롤 허용
        return Math.min(1, Math.max(0.1, sW));
    }, [containerWidth, contentWidthPx, scale]);
    const effectiveScale = fitBoth ? computedFitScale : scale;
	const rulerPx = 34; // ruler width on each side (slightly wider for readability)
	const rulerLabelFontPx = 14;
	const [showRuler, setShowRuler] = useState<boolean>(true);
    const [showGuides, setShowGuides] = useState<boolean>(true);
	const [guide1Mm, setGuide1Mm] = useState<number>(80);
	const [guide2Mm, setGuide2Mm] = useState<number>(50);
	// print calibration
	const [printScalePercent, setPrintScalePercent] = useState<number>(100);
	const [printOffsetXmm, setPrintOffsetXmm] = useState<number>(0);
	const [printOffsetYmm, setPrintOffsetYmm] = useState<number>(0);
	const [applyCalibrationToDownload, setApplyCalibrationToDownload] = useState<boolean>(false);

    // environment settings
	const [envOpen, setEnvOpen] = useState<boolean>(false);
    const [envDefaultPreset, setEnvDefaultPreset] = useState<string>("bouquet-38x400");
    // font environment
    const [envFontSource, setEnvFontSource] = useState<"system" | "web">("system");
    const [envSystemFont, setEnvSystemFont] = useState<string>("Noto Sans KR");
    const [envWebFontUrl, setEnvWebFontUrl] = useState<string>("");
    const [envWebFontFamily, setEnvWebFontFamily] = useState<string>("");
    type WebFontItem = { id: string; url: string; family: string };
    const [envWebFonts, setEnvWebFonts] = useState<WebFontItem[]>([
        { id: "noto-sans-kr", url: "https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;700&display=swap", family: "Noto Sans KR" },
        { id: "nanum-gothic", url: "https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@400;700&display=swap", family: "Nanum Gothic" },
        { id: "nanum-myeongjo", url: "https://fonts.googleapis.com/css2?family=Nanum+Myeongjo:wght@400;700&display=swap", family: "Nanum Myeongjo" },
        { id: "gowun-dodum", url: "https://fonts.googleapis.com/css2?family=Gowun+Dodum&display=swap", family: "Gowun Dodum" },
        { id: "do-hyeon", url: "https://fonts.googleapis.com/css2?family=Do+Hyeon&display=swap", family: "Do Hyeon" },
        { id: "noto-serif-kr", url: "https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;700&display=swap", family: "Noto Serif KR" },
        { id: "black-han-sans", url: "https://fonts.googleapis.com/css2?family=Black+Han+Sans&display=swap", family: "Black Han Sans" },
        { id: "east-sea-dokdo", url: "https://fonts.googleapis.com/css2?family=East+Sea+Dokdo&display=swap", family: "East Sea Dokdo" },
        { id: "jua", url: "https://fonts.googleapis.com/css2?family=Jua&display=swap", family: "Jua" },
        { id: "gamja-flower", url: "https://fonts.googleapis.com/css2?family=Gamja+Flower&display=swap", family: "Gamja Flower" }
    ]);
    // Custom raw CSS (@font-face) entries
    type WebFontCssItem = { id: string; css: string; families: string[] };
    const [envWebFontCss, setEnvWebFontCss] = useState<string>("");
    const [envWebFontCssList, setEnvWebFontCssList] = useState<WebFontCssItem[]>([
        {
            id: "chosun-gs",
            css: `@font-face {
                font-family: 'ChosunGs';
                src: url('https://fastly.jsdelivr.net/gh/projectnoonnu/noonfonts_20-04@1.0/ChosunGs.woff') format('woff');
                font-weight: normal;
                font-style: normal;
                font-display: swap;
            }`,
            families: ["ChosunGs"]
        },
        {
            id: "korean-calligraphy",
            css: `@font-face {
                font-family: 'Yeon Sung';
                src: url('https://fonts.googleapis.com/css2?family=Yeon+Sung&display=swap');
                font-weight: 400;
                font-style: normal;
                font-display: swap;
            }`,
            families: ["Yeon Sung"]
        }
    ]);
    const [fontLoadTick, setFontLoadTick] = useState<number>(0);
	const [envPrintScale, setEnvPrintScale] = useState<number>(100);
	const [envOffsetXmm, setEnvOffsetXmm] = useState<number>(0);
	const [envOffsetYmm, setEnvOffsetYmm] = useState<number>(0);
    // global base font
    const koreanFontOptions = [
        { key: 'Noto Sans KR', label: 'Noto Sans KR (기본 고딕)' },
        { key: 'Nanum Gothic', label: '나눔고딕 (Nanum Gothic)' },
        { key: 'Nanum Myeongjo', label: '나눔명조 (Nanum Myeongjo)' },
        { key: 'Gowun Dodum', label: '고운돋움 (Gowun Dodum)' },
        { key: 'Do Hyeon', label: '도현 (Do Hyeon)' },
        { key: 'Noto Serif KR', label: 'Noto Serif KR (명조체)' },
        { key: 'Black Han Sans', label: 'Black Han Sans (두꺼운 고딕)' },
        { key: 'Jua', label: 'Jua (둥근 고딕)' },
        { key: 'East Sea Dokdo', label: 'East Sea Dokdo (손글씨)' },
        { key: 'Gamja Flower', label: 'Gamja Flower (귀여운 손글씨)' },
        { key: 'ChosunGs', label: '조선일보명조 (ChosunGs)' },
        { key: 'Yeon Sung', label: '연성 (서예체)' },
    ];
    const windowsFontOptions = [
        { key: 'Malgun Gothic', label: '맑은 고딕 (Malgun Gothic)' },
        { key: 'Gulim', label: '굴림 (Gulim)' },
        { key: 'Dotum', label: '돋움 (Dotum)' },
        { key: 'Batang', label: '바탕 (Batang)' },
        { key: 'Gungsuh', label: '궁서 (Gungsuh)' },
        { key: 'Microsoft YaHei', label: 'Microsoft YaHei (중국어)' },
        { key: 'SimSun', label: 'SimSun (중국어 명조)' },
        { key: 'MS Gothic', label: 'MS Gothic (일본어)' },
        { key: 'Yu Gothic', label: 'Yu Gothic (일본어 고딕)' },
    ];
    const latinFontOptions = [
        { key: 'Arial', label: 'Arial (기본 산세리프)' },
        { key: 'Times New Roman', label: 'Times New Roman (세리프)' },
        { key: 'Courier New', label: 'Courier New (모노스페이스)' },
        { key: 'Georgia', label: 'Georgia (세리프)' },
        { key: 'Verdana', label: 'Verdana (웹 고딕)' },
        { key: 'Tahoma', label: 'Tahoma (시스템 고딕)' },
        { key: 'Trebuchet MS', label: 'Trebuchet MS (둥근 고딕)' },
        { key: 'Inter', label: 'Inter (모던 고딕)' },
        { key: 'Roboto', label: 'Roboto (구글 고딕)' },
        { key: 'Noto Sans', label: 'Noto Sans (국제 고딕)' },
        { key: 'Helvetica', label: 'Helvetica (클래식)' },
        { key: 'Calibri', label: 'Calibri (오피스)' },
        { key: 'Segoe UI', label: 'Segoe UI (윈도우)' },
        { key: 'San Francisco', label: 'San Francisco (맥OS)' },
    ];
    // Experimental: Local Font Access (Chromium) — enumerate installed system fonts with permission
    const [systemFontList, setSystemFontList] = useState<string[]>([]);
    const [loadingSystemFonts, setLoadingSystemFonts] = useState<boolean>(false);
    const [systemFontError, setSystemFontError] = useState<string>("");
    const loadSystemFonts = async () => {
        setSystemFontError("");
        try {
            const navAny = navigator as { fonts?: { query?: () => Promise<{ family?: string; fullName?: string }[]> } };
            if (!navAny.fonts || !navAny.fonts.query) {
                setSystemFontError("브라우저가 시스템 폰트 열람을 지원하지 않습니다(Chrome 기반 권장).");
                return;
            }
            setLoadingSystemFonts(true);
            const fonts = await navAny.fonts.query();
            const names = new Set<string>();
            // FontData has properties: postscriptName, fullName, family, style
            for await (const f of fonts) {
                if (f.fullName) names.add(String(f.fullName));
                else if (f.family) names.add(String(f.family));
            }
            const arr = Array.from(names).sort((a,b)=>a.localeCompare(b));
            setSystemFontList(arr);
        } catch {
            setSystemFontError("시스템 폰트 접근이 거부되었거나 실패했습니다.");
        } finally {
            setLoadingSystemFonts(false);
        }
    };
    const [baseFontFamily, setBaseFontFamily] = useState<string>(koreanFontOptions[0].key);
    const [baseFontSizePx, setBaseFontSizePx] = useState<number>(32);
    // Global per-script font selection
    const [fontKorean, setFontKorean] = useState<string>("ChosunGs");
    const [fontCjk, setFontCjk] = useState<string>("ChosunGs");
    const [fontLatin, setFontLatin] = useState<string>("Arial");

    // Ribbon Print Settings
    const [printDialogOpen, setPrintDialogOpen] = useState<boolean>(false);
    const [printMode, setPrintMode] = useState<'left' | 'right' | 'both'>('both');
    const [selectedPrinter, setSelectedPrinter] = useState<string>('');
    const [printCopies, setPrintCopies] = useState<number>(1);
    const [isRollRibbon, setIsRollRibbon] = useState<boolean>(true);
    const [showCutLine, setShowCutLine] = useState<boolean>(false); // 좌우 구분선
    const [printSpeed, setPrintSpeed] = useState<'normal' | 'slow'>('normal');
    const [xOffset, setXOffset] = useState<number>(0);
    const [postFeed, setPostFeed] = useState<number>(100); // 롤리본 여분 배출량
    
    // Windows installed printers
    const [installedPrinters, setInstalledPrinters] = useState<string[]>([]);
    const [loadingPrinters, setLoadingPrinters] = useState<boolean>(false);
    
    // Multi Ribbon Batch Printing
    const [ribbonBatch, setRibbonBatch] = useState<Array<{
        id: string;
        leftContent: string;
        rightContent: string;
        enabled: boolean;
    }>>([
        { id: '1', leftContent: '경조사어 리본', rightContent: '보내는이\n[회사명]', enabled: true },
        { id: '2', leftContent: '축하합니다', rightContent: '○○○님', enabled: false },
        { id: '3', leftContent: '감사합니다', rightContent: '△△△님', enabled: false },
    ]);
    const [batchMode, setBatchMode] = useState<boolean>(false);
    const [ribbonSpacingMm, setRibbonSpacingMm] = useState<number>(20); // 리본 간 간격
    
    // Get Windows installed printers
    const getInstalledPrinters = async () => {
        setLoadingPrinters(true);
        try {
            // 방법 3: 폴백 - 일반적인 프린터 목록
            const fallbackPrinters = [
                '기본 프린터',
                'Microsoft Print to PDF',
                'Microsoft XPS Document Writer',
                'Fax',
                '사용자 정의 프린터'
            ];
            
            setInstalledPrinters(fallbackPrinters);
            if (fallbackPrinters.length > 0 && !selectedPrinter) {
                setSelectedPrinter(fallbackPrinters[0]);
            }
            
        } catch (error) {
            console.error('프린터 목록 가져오기 실패:', error);
            setInstalledPrinters(['기본 프린터']);
            setSelectedPrinter('기본 프린터');
        } finally {
            setLoadingPrinters(false);
        }
    };

    const leftCanvasRef = useRef<HTMLCanvasElement | null>(null);
    const rightCanvasRef = useRef<HTMLCanvasElement | null>(null);
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const leftPanelRef = useRef<HTMLDivElement | null>(null);
    const [leftPanelHeight, setLeftPanelHeight] = useState<number>(0);

    // Presets (editable list)
    type RibbonPreset = {
        key: string;
        label: string; // 리본이름
        width: number; // 넓이(mm)
        length: number; // 길이(mm)
        laceMm: number; // 레이스(양옆 여백)
        topMm: number; // 상단(mm)
        bottomMm: number; // 하단(mm)
        bracketPercent: number; // 축소비율(%)
        scaleXPercent: number; // 가로비율(%)
        scaleYPercent: number; // 세로비율(%)
        marginMm: number; // 여백(mm) - 참고용
        startXmm: number; // 가로시작(mm)
        startYmm: number; // 세로시작(mm)
    };
    const defaultPresets: RibbonPreset[] = [
        { key: "bouquet-38x400", label: "꽃다발 38x400mm", width: 38, laceMm: 5, length: 400, topMm: 80, bottomMm: 50, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 53, startXmm: 0, startYmm: 0 },
        { key: "dongyang-45x450", label: "동양란 45x450mm", width: 45, laceMm: 7, length: 450, topMm: 100, bottomMm: 50, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 57, startXmm: 0, startYmm: 0 },
        { key: "dongyang-50x500", label: "동양란 50x500mm", width: 50, laceMm: 8, length: 500, topMm: 120, bottomMm: 50, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 62, startXmm: 0, startYmm: 0 },
        { key: "eastwest-55x500", label: "동/서양란 55x500mm", width: 55, laceMm: 10, length: 500, topMm: 120, bottomMm: 80, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 65, startXmm: 0, startYmm: 0 },
        { key: "seoyang-60x600", label: "서양란 60x600mm", width: 60, laceMm: 10, length: 600, topMm: 150, bottomMm: 80, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 70, startXmm: 0, startYmm: 0 },
        { key: "yeonghwa-70x750", label: "영화(죽) 70x750mm", width: 70, laceMm: 10, length: 750, topMm: 150, bottomMm: 100, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 70, startXmm: 0, startYmm: 0 },
        { key: "janghak-95x1000", label: "장학나무 95x1000mm", width: 95, laceMm: 10, length: 1000, topMm: 150, bottomMm: 100, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 80, startXmm: 0, startYmm: 0 },
        { key: "flower-large-105x1100", label: "화분 大 105/110x1100mm", width: 105, laceMm: 23, length: 1100, topMm: 150, bottomMm: 100, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 87, startXmm: 0, startYmm: 0 },
        { key: "flower-mid-85x1000", label: "화분 中 85x1000mm", width: 85, laceMm: 23, length: 1000, topMm: 150, bottomMm: 100, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 102, startXmm: 0, startYmm: 0 },
        { key: "flower-small-70x900", label: "화분 小 70x900mm", width: 70, laceMm: 23, length: 900, topMm: 150, bottomMm: 100, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 110, startXmm: 0, startYmm: 0 },
        { key: "funeral-large-150x1800", label: "근조 大 150x1800mm", width: 150, laceMm: 23, length: 1800, topMm: 150, bottomMm: 350, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 92, startXmm: 0, startYmm: 0 },
        { key: "funeral-2-115x1200", label: "근조 2단 115x1200mm", width: 115, laceMm: 23, length: 1200, topMm: 250, bottomMm: 150, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 112, startXmm: 0, startYmm: 0 },
        { key: "funeral-2-135x1700", label: "근조 2단 135x1700mm", width: 135, laceMm: 23, length: 1700, topMm: 350, bottomMm: 150, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 112, startXmm: 0, startYmm: 0 },
        { key: "funeral-3-165x2200", label: "근조 3단 165x2200mm", width: 165, laceMm: 23, length: 2200, topMm: 400, bottomMm: 300, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 117, startXmm: 0, startYmm: 0 },
        { key: "chukhwa-3-165x2200", label: "축화 3단 165x2200mm", width: 165, laceMm: 23, length: 2200, topMm: 400, bottomMm: 300, bracketPercent: 70, scaleXPercent: 100, scaleYPercent: 100, marginMm: 117, startXmm: 0, startYmm: 0 },
    ];
    const [presets, setPresets] = useState<RibbonPreset[]>(defaultPresets);
    const [selectedPreset, setSelectedPreset] = useState<string>(defaultPresets[0].key);
    const [presetOpen, setPresetOpen] = useState<boolean>(false);
    const getPresetDisplayLabel = (p: RibbonPreset) => (p.label && p.label.trim().length > 0) ? p.label : `${p.width}x${p.length}mm`;


    // Celebration samples (경조사) — categories and items
    type SampleItem = { label: string; value: string };
    type SampleCategory = { key: string; name: string; items: SampleItem[] };
    const [samples, setSamples] = useState<SampleCategory[]>([]);
    const [leftSampleCat, setLeftSampleCat] = useState<string>("");
    // Sender samples (for right ribbon)
    const [senderSamples, setSenderSamples] = useState<SampleCategory[]>([]);
    const [rightSenderCat, setRightSenderCat] = useState<string>("");


    const RAW_SAMPLES = `==========  생일, 회갑, 칠순, 팔순, 구순  
祝生日=축생일
祝生辰=축생신
祝華甲=축화갑(60세)
祝壽宴=축수연(60세)
祝回甲=축회갑(60세)
祝古稀=축고희(70세)
祝七旬=축칠순(70세)
祝喜壽=축희수(77세)
祝八旬=축팔순(80세)
祝傘壽=축산수(80세)
祝米壽=축미수(88세)
祝白壽=축백수(99세)
Happy Birthday!=생일을 축하합니다
==========  승진. 취임. 영전  
祝昇進=축승진
祝榮轉=축영전
祝就任=축위임
祝轉任=축전임
祝移任=축이임
祝遷任=축천임
祝轉役=축전역
祝榮進=축영진
祝選任=축선임
祝重任=축중임
祝連任=축연임
祝就任=축취임
Congratulations on your promotion=승진을 축하합니다
==========  개업, 창립  
祝發展=축발전
祝開業=축개업
祝盛業=축성업
祝繁榮=축번영
祝創立=축창립
祝設立=축설립
祝創設=축창설
祝創刊=축창간
祝移轉=축이전
祝開院=축개원
祝開館=축개관
祝開場=축개장
祝開店=축개점
祝創立紀念紀念=축창립기념기념
祝創立00周年=축창립00주년
Congratulations on your new business=개업을 축하합니다
==========  약혼, 결혼, 결혼기념일  
祝約婚=축약혼
祝結婚=축결혼 (男)
祝華婚=축화혼 (女)
祝成婚=축성혼
紙婚式=지혼식 1주년 결혼기념식
常婚式=상혼식 2주년 결혼기념식
菓婚式=과혼식 3주년 결혼기념식
革婚式=혁혼식 4주년 결혼기념식
木婚式=목혼식 5주년 결혼기념식
花婚式=화혼식 7주년 결혼기념식
祝錫婚式=축석혼식 10주년 결혼기념식
痲婚式=마혼식 12주년 결혼기념식
祝銅婚式=축동혼식 15주년 결혼기념식
祝陶婚式=축도혼식 20주년 결혼기념식
祝銀婚式=축은혼식 25주년 결혼기념식
祝眞珠婚式=축진주혼식 30주년 결혼기념식
祝珊瑚婚式=축산호혼식 35주년 결혼기념식
祝錄玉婚式=축녹옥혼식 40주년 결혼기념식
祝紅玉婚式=축홍옥혼식 45주년 결혼기념식
祝金婚式=축금혼식 50주년 결혼기념식
祝金剛婚式=축금강혼식 60주년 결혼기념식
A Happy Marriage=행복한 결혼되세요
Congratulations on your 10th anniversary=결혼 10주년을 축하합니다
==========   죽음애도   
謹弔=근조
追慕=추모
追悼=추도
哀悼=애도
弔意=조의
尉靈=위령
謹悼=근도
賻儀=부의
冥福=명복
故人의 冥福을 빕니다
삼가 故人의 冥福을 빕니다
You have my condolences=삼가 고인의 명복을 빕니다
Please accept my deepest condolences=깊은 애도를 표합니다
==========  출산, 순산  
祝順産=축순산
祝出産=축출산
祝誕生=축탄생
祝得男=축득남
祝得女=축득녀
祝公主誕生=축공주탄생
祝王子誕生=축왕자탄생
Congratulations on your new baby=출산을 축하합니다
`;

    const hasHanja = (s: string) => /[\u4E00-\u9FFF]/.test(s);
    const preferHanjaFromLabel = (label: string, fallback: string) => {
        const parts = label.split('/').map(p => p.trim());
        if (parts.length >= 2) {
            const a = parts[0];
            const b = parts[1];
            if (hasHanja(a) && !hasHanja(b)) return a;
            if (hasHanja(b) && !hasHanja(a)) return b;
            return a; // default left
        }
        return fallback;
    };

    const parseSamples = (raw: string): SampleCategory[] => {
        const lines = raw.split(/\r?\n/);
        const result: SampleCategory[] = [];
        let current: SampleCategory | null = null;
        for (const line0 of lines) {
            const line = line0.trim();
            if (!line) continue;
            if (line.startsWith("==========")) {
                const name = line.replace(/=+/g, "").trim();
                const key = `cat_${result.length}`;
                current = { key, name, items: [] };
                result.push(current);
                continue;
            }
            if (!current) continue;
            const eqIdx = line.indexOf('=');
            if (eqIdx > -1) {
                const left = line.slice(0, eqIdx).trim();
                const right = line.slice(eqIdx + 1).trim();
                let preferred = left;
                if (hasHanja(right) && !hasHanja(left)) preferred = right;
                current.items.push({ label: `${left} / ${right}`.trim(), value: preferred });
            } else {
                current.items.push({ label: line, value: line });
            }
        }
        return result;
    };

    // load presets from localStorage with migration/merge to full defaults
    useEffect(() => {
        try {
            const raw = localStorage.getItem('ribbonPresetListV1');
            if (raw) {
                const list0 = JSON.parse(raw) as RibbonPreset[];
                const list = Array.isArray(list0) ? list0 : [];
                // normalize stored
                const normalizedStored = (list.length > 0 ? list : []).map((p, i) => ({
                    key: p.key || `custom-${Date.now()}-${i}`,
                    label: String(p.label || '').trim() || `${p.width}x${p.length}mm`,
                    width: Number(p.width) || 38,
                    length: Number(p.length) || 400,
                    laceMm: Number(p.laceMm) || 0,
                    topMm: Number(p.topMm) || 0,
                    bottomMm: Number(p.bottomMm) || 0,
                    bracketPercent: Number(p.bracketPercent) || 70,
                    scaleXPercent: Number(p.scaleXPercent) || 100,
                    scaleYPercent: Number(p.scaleYPercent) || 100,
                    marginMm: Number(p.marginMm) || 0,
                    startXmm: Number(p.startXmm) || 0,
                    startYmm: Number(p.startYmm) || 0,
                }));
                // merge defaults that are missing
                const keyOf = (p: RibbonPreset) => `${p.label}|${p.width}x${p.length}`;
                const map = new Map<string, RibbonPreset>();
                for (const p of normalizedStored) map.set(keyOf(p), p);
                for (const d of defaultPresets) {
                    const kd = keyOf(d);
                    if (!map.has(kd)) map.set(kd, d);
                }
                const merged = Array.from(map.values());
                // sort by width then length then label
                merged.sort((a,b)=> a.width-b.width || a.length-b.length || a.label.localeCompare(b.label));
                setPresets(merged);
                const firstKey = (merged[0]?.key) || defaultPresets[0].key;
                setSelectedPreset(firstKey);
                applyPreset(firstKey);
                // persist merged if different size
                if (merged.length !== list.length) localStorage.setItem('ribbonPresetListV1', JSON.stringify(merged));
            } else {
                localStorage.setItem('ribbonPresetListV1', JSON.stringify(defaultPresets));
                setPresets(defaultPresets);
                setSelectedPreset(defaultPresets[0].key);
                applyPreset(defaultPresets[0].key);
            }
        } catch {
            // fallback to defaults on any error
            setPresets(defaultPresets);
            setSelectedPreset(defaultPresets[0].key);
            applyPreset(defaultPresets[0].key);
            try { localStorage.setItem('ribbonPresetListV1', JSON.stringify(defaultPresets)); } catch {}
        }
    }, []);

    const savePresets = (list: RibbonPreset[]) => {
        const normalized = list.map((p, i) => ({
            ...p,
            key: p.key || `custom-${Date.now()}-${i}`,
            label: String(p.label || '').trim() || `${p.width}x${p.length}mm`,
        }));
        setPresets(normalized);
        localStorage.setItem('ribbonPresetListV1', JSON.stringify(normalized));
    };

    // load samples
    useEffect(() => {
        try {
            const raw = localStorage.getItem('ribbonSamplesV1');
            if (raw) {
                const parsed = JSON.parse(raw) as SampleCategory[];
                // upgrade: recompute preferred values by hanja priority from label when possible
                const upgraded = parsed.map(cat => ({
                    ...cat,
                    items: cat.items.map(it => {
                        const preferred = preferHanjaFromLabel(it.label, it.value);
                        return { ...it, value: preferred };
                    })
                }));
                setSamples(upgraded);
                localStorage.setItem('ribbonSamplesV1', JSON.stringify(upgraded));
                if (upgraded[0]) {
                    setLeftSampleCat(upgraded[0].key);
                }
            } else {
                const parsed = parseSamples(RAW_SAMPLES);
                setSamples(parsed);
                localStorage.setItem('ribbonSamplesV1', JSON.stringify(parsed));
                if (parsed[0]) {
                    setLeftSampleCat(parsed[0].key);
                }
            }
        } catch {}
    }, []);

    // load sender samples (right)
    const RAW_SENDER_SAMPLES = `==========  보내는이 선택
(주)삼성전자[대표이사/홍길동]임원일동
LG전자[이사]홍길동
삼성SDS[과장]홍길동
현대자동차[부장]이순신
GM[이사]홍길동
현대건설[사장]홍길동`;

    useEffect(() => {
        try {
            const raw = localStorage.getItem('ribbonSenderSamplesV1');
            if (raw) {
                const parsed = JSON.parse(raw) as SampleCategory[];
                setSenderSamples(parsed);
                if (parsed[0]) setRightSenderCat(parsed[0].key);
            } else {
                const parsed = parseSamples(RAW_SENDER_SAMPLES);
                setSenderSamples(parsed);
                localStorage.setItem('ribbonSenderSamplesV1', JSON.stringify(parsed));
                if (parsed[0]) setRightSenderCat(parsed[0].key);
            }
        } catch {}
    }, []);



	const drawRibbon = (canvas: HTMLCanvasElement | null, settings: RibbonTextSettings) => {
		if (!canvas) return;
		const totalWidth = rulerPx + ribbonWidthPx + rulerPx;
		canvas.width = totalWidth;
		canvas.height = ribbonLengthPx;
		const ctx = canvas.getContext("2d");
		if (!ctx) return;

		// background gray
		ctx.fillStyle = "#e5e7eb"; // gray-200
		ctx.fillRect(0, 0, totalWidth, ribbonLengthPx);

		// rulers
		const drawRuler = (xStart: number) => {
            ctx.fillStyle = "#22c55e"; // green-500
            ctx.fillRect(xStart, 0, rulerPx, ribbonLengthPx);
            ctx.strokeStyle = "#0f766e"; // darker lines
            ctx.lineWidth = 1.25;
            ctx.font = `600 ${rulerLabelFontPx}px Arial`;
            for (let mm = 0; mm <= ribbonLengthMm; mm += 10) {
                const y = Math.round(mmToPx(mm));
                ctx.beginPath();
                ctx.moveTo(xStart, y);
                const tick = mm % 50 === 0 ? 14 : mm % 10 === 0 ? 9 : 5;
                ctx.lineTo(xStart + tick, y);
                ctx.stroke();
                if (mm % 50 === 0 && mm !== 0) {
                    // outline then fill to improve contrast over green
                    ctx.save();
                    ctx.lineWidth = 3;
                    ctx.strokeStyle = "#ffffff";
                    ctx.strokeText(`${mm}mm`, xStart + 14, y - rulerLabelFontPx / 3);
                    ctx.fillStyle = "#111111";
                    ctx.fillText(`${mm}mm`, xStart + 14, y - rulerLabelFontPx / 3);
                    ctx.restore();
                }
            }
        };
		if (showRuler) {
			drawRuler(0);
			drawRuler(rulerPx + ribbonWidthPx);
		}

		// ribbon center area
		const ribbonX = rulerPx;
		ctx.fillStyle = backgroundColor;
		ctx.fillRect(ribbonX, 0, ribbonWidthPx, ribbonLengthPx);

		// center guide lines
		ctx.strokeStyle = "#60a5fa"; // blue-400
		ctx.setLineDash([4, 4]);
		ctx.beginPath();
		ctx.moveTo(ribbonX + ribbonWidthPx / 2, 0);
		ctx.lineTo(ribbonX + ribbonWidthPx / 2, ribbonLengthPx);
		ctx.stroke();
		ctx.setLineDash([]);

		// reference dimension lines (customizable)
		if (showGuides) {
			ctx.save();
			ctx.strokeStyle = "#111827";
			ctx.lineWidth = 1.5;
			ctx.setLineDash([3, 6]);
			const y1 = mmToPx(guide1Mm);
			ctx.beginPath();
			ctx.moveTo(ribbonX, y1);
			ctx.lineTo(ribbonX + ribbonWidthPx, y1);
			ctx.stroke();
			ctx.setLineDash([]);
			ctx.font = "700 14px Arial";
			ctx.fillStyle = "#111827";
			ctx.textAlign = "right";
			ctx.textBaseline = "middle";
			ctx.fillText(`${guide1Mm}mm`, ribbonX + ribbonWidthPx - 4, y1);
			const y2b = ribbonLengthPx - mmToPx(guide2Mm);
			ctx.setLineDash([3, 6]);
			ctx.beginPath();
			ctx.moveTo(ribbonX, y2b);
			ctx.lineTo(ribbonX + ribbonWidthPx, y2b);
			ctx.stroke();
			ctx.setLineDash([]);
			ctx.fillText(`${guide2Mm}mm`, ribbonX + ribbonWidthPx - 4, y2b);
			ctx.restore();
		}

		// vertical text with auto-fit to ribbon width
		const fontWeight = settings.isBold ? "700" : "400";
		const fontStyle = settings.isItalic ? "italic" : "normal";
		ctx.fillStyle = settings.color;

		const sidePaddingPx = Math.max(0, mmToPx(settings.sidePaddingMm));
		const targetInnerWidth = Math.max(1, ribbonWidthPx - sidePaddingPx * 2);

		// Visualize side padding (레이스) areas on both edges
		if (sidePaddingPx > 0) {
			ctx.save();
			ctx.fillStyle = "rgba(148,163,184,0.18)"; // slate-400 at low opacity
			// left lace
			ctx.fillRect(ribbonX, 0, sidePaddingPx, ribbonLengthPx);
			// right lace
			ctx.fillRect(ribbonX + ribbonWidthPx - sidePaddingPx, 0, sidePaddingPx, ribbonLengthPx);
			// inner guide lines for lace boundary
			ctx.strokeStyle = "#94a3b8"; // slate-400
			ctx.setLineDash([4,3]);
			ctx.beginPath();
			ctx.moveTo(ribbonX + sidePaddingPx, 0);
			ctx.lineTo(ribbonX + sidePaddingPx, ribbonLengthPx);
			ctx.moveTo(ribbonX + ribbonWidthPx - sidePaddingPx, 0);
			ctx.lineTo(ribbonX + ribbonWidthPx - sidePaddingPx, ribbonLengthPx);
			ctx.stroke();
			ctx.setLineDash([]);
			ctx.restore();
		}

		// per-script font helpers
		const isHangulChar = (ch: string) => /[\u1100-\u11FF\uAC00-\uD7AF]/.test(ch);
		const isHanjaChar = (ch: string) => /[\u4E00-\u9FFF]/.test(ch);
		const isLatinChar = (ch: string) => /[A-Za-z0-9]/.test(ch);
		const fontChainForChar = (ch: string) => {
			if (isHangulChar(ch)) return `"${fontKorean}", "${baseFontFamily}", sans-serif`;
			if (isHanjaChar(ch)) return `"${fontCjk}", "${baseFontFamily}", sans-serif`;
			if (isLatinChar(ch)) return `"${fontLatin}", "${baseFontFamily}", sans-serif`;
			return `"${baseFontFamily}", sans-serif`;
		};

		// measure widest unit at current font size (treat (X) as one unit)
		const baseFontSize = baseFontSizePx;
        const measureUnits: string[] = [];
        {
            const s = settings.content;
            let i = 0;
            while (i < s.length) {
                if (s[i] === '(') {
                    const j = s.indexOf(')', i + 1);
                    if (j > i && j - i - 1 === 1) { measureUnits.push(s[i + 1]); i = j + 1; continue; }
                }
                measureUnits.push(s[i]); i++;
            }
        }
        let maxCharWidth = 1;
        for (const u of measureUnits) {
			ctx.font = `${fontStyle} ${fontWeight} ${baseFontSize}px ${fontChainForChar(u)}`;
			const w = ctx.measureText(u).width;
            if (w > maxCharWidth) maxCharWidth = w;
        }

        let usedFontSize = baseFontSize;
        if (settings.autoFit && maxCharWidth > 0) {
            const slashIdx = settings.content.indexOf('/');
            const perColumnWidth = slashIdx >= 0 ? Math.max(1, (targetInnerWidth / 2) - 4) : targetInnerWidth;
            // Fit ignoring scaleX so that scaleX directly scales visual width (e.g., 50% halves width)
            const scaleW = perColumnWidth / Math.max(1, maxCharWidth);
            usedFontSize = Math.max(8, Math.min(400, Math.floor(baseFontSize * scaleW)));
        }
		ctx.textBaseline = "top";
		ctx.textAlign = "center";


		const topMarginPx = mmToPx(settings.topMarginMm);
		const bottomMarginPx = mmToPx(settings.bottomMarginMm);
		const availableHeight = ribbonLengthPx - topMarginPx - bottomMarginPx;

		// draw top/bottom margin guide lines
		ctx.save();
		ctx.strokeStyle = "#ef4444"; // red-500
		ctx.lineWidth = 2;
		ctx.setLineDash([6, 4]);
		// top margin line
		ctx.beginPath();
		ctx.moveTo(ribbonX, topMarginPx);
		ctx.lineTo(ribbonX + ribbonWidthPx, topMarginPx);
		ctx.stroke();
		// bottom margin line
		const bottomY = ribbonLengthPx - bottomMarginPx;
		ctx.beginPath();
		ctx.moveTo(ribbonX, bottomY);
		ctx.lineTo(ribbonX + ribbonWidthPx, bottomY);
		ctx.stroke();
		// labels for margins (mm)
		ctx.setLineDash([]);
		ctx.fillStyle = "#ef4444";
		ctx.font = "600 12px Arial";
		ctx.textAlign = "right";
		ctx.textBaseline = "bottom";
		ctx.fillText(`${Math.round(settings.topMarginMm)}mm`, ribbonX + ribbonWidthPx - 4, topMarginPx - 2);
		ctx.textBaseline = "top";
		ctx.fillText(`${Math.round(settings.bottomMarginMm)}mm`, ribbonX + ribbonWidthPx - 4, bottomY + 2);
		ctx.restore();

		// Build tokens with optional bracket scaling (no special '/' handling inside brackets for now)
        type Token = { ch: string; factor: number; col?: 'left' | 'right' };
        const tokens: Token[] = [];
        const bracketFactor = Math.max(0.05, settings.bracketScale ?? 0.5);
        const bracketSpacer = Math.max(0, settings.bracketSpacerFactor ?? 0.5);
        for (let i = 0; i < settings.content.length; ) {
            const ch = settings.content[i];
            if (ch === '[') {
                // Parse until matching ']'
                let j = i + 1;
                let buf = '';
                while (j < settings.content.length && settings.content[j] !== ']') { buf += settings.content[j]; j++; }
                if (j < settings.content.length && settings.content[j] === ']') {
					if (settings.applyBracketScale) tokens.push({ ch: '', factor: bracketSpacer });
					for (const c of buf) tokens.push({ ch: c, factor: settings.applyBracketScale ? bracketFactor : 1 });
					if (settings.applyBracketScale) tokens.push({ ch: '', factor: bracketSpacer });
                    i = j + 1; continue;
                }
            }
            if (ch === '(') {
                const j = settings.content.indexOf(')', i + 1);
                if (j > i && j - i - 1 === 1) { tokens.push({ ch: settings.content.slice(i, j + 1), factor: 1 }); i = j + 1; continue; }
            }
            tokens.push({ ch, factor: 1 });
            i++;
        }

        const charHeight = usedFontSize;
        const baseGlyphScaleY = Math.max(0.1, settings.scaleY);
        const baseGlyphScaleX = Math.max(0.1, settings.scaleX);
        const baselineSpacing = mmToPx(settings.charSpacingMm);
        const n = tokens.length;
        let spacingDevice = baselineSpacing;
        // sum of base heights with token factor and base scaleY
        const sumBase = tokens.reduce((acc, t) => acc + charHeight * baseGlyphScaleY * t.factor, 0);
        if (n > 1) {
            const needed = sumBase + (n - 1) * baselineSpacing;
            if (needed <= availableHeight) {
                spacingDevice = baselineSpacing + (availableHeight - needed) / (n - 1);
            } else {
                spacingDevice = 0;
            }
        } else {
            spacingDevice = 0;
        }
        // additional uniform Y scale so that total exactly fits if still larger
        const totalWithZeroSpacing = sumBase + (n - 1) * spacingDevice;
        let additionalScale = 1;
        if (totalWithZeroSpacing > availableHeight && sumBase > 0) {
            additionalScale = Math.max(0.05, availableHeight / sumBase);
        }
        const tokenHeights = tokens.map(t => {
            if (t.ch && t.ch.startsWith('(') && t.ch.endsWith(')') && t.ch.length === 3) {
                // (X) as one unit: height should be based on inner glyph only (no extra space)
                return charHeight * baseGlyphScaleY * 1 * additionalScale;
            }
            return charHeight * baseGlyphScaleY * t.factor * additionalScale;
        });
        const totalHeight = tokenHeights.reduce((a,b)=>a+b,0) + (n - 1) * spacingDevice;
        const yStartDevice = settings.verticalDirection === 'bottom-up'
            ? topMarginPx + availableHeight - (totalHeight - (n>0?0:0))
            : topMarginPx;

        // horizontal alignment position
        let anchorX = ribbonX + Math.round(ribbonWidthPx / 2);
        if (settings.horizontalAlign === "left") {
            anchorX = ribbonX + sidePaddingPx;
            ctx.textAlign = "left";
        } else if (settings.horizontalAlign === "right") {
            anchorX = ribbonX + ribbonWidthPx - sidePaddingPx;
            ctx.textAlign = "right";
        } else {
            ctx.textAlign = "center";
        }
        // helper: token-specific horizontal scale for (X) so that it never exceeds inner width
		const isParenSingle = (s?: string) => !!s && s.startsWith('(') && s.endsWith(')') && s.length === 3;


        ctx.save();
        // two-column rendering when '/' exists
        const slashPos = settings.content.indexOf('/');
        if (slashPos >= 0) {
            const drawStream = (text: string, x: number, align: CanvasTextAlign, innerWidth: number) => {
                // build tokens for the stream
                const streamTokens: { ch: string; factor: number }[] = [];
                let inB = false;
                for (let i = 0; i < text.length; ) {
                    const c = text[i];
                    if (c === '[') { if (settings.applyBracketScale) streamTokens.push({ ch: '', factor: bracketSpacer }); inB = true; i++; continue; }
                    if (c === ']') { if (settings.applyBracketScale) streamTokens.push({ ch: '', factor: bracketSpacer }); inB = false; i++; continue; }
                    if (c === '(') { const j = text.indexOf(')', i + 1); if (j > i && j - i - 1 === 1) { streamTokens.push({ ch: text.slice(i, j + 1), factor: 1 }); i = j + 1; continue; } }
                    streamTokens.push({ ch: c, factor: inB && (settings.applyBracketScale ?? false) ? bracketFactor : 1 }); i++;
                }
                // layout
                const sumBaseS = streamTokens.reduce((acc,t)=>acc + charHeight * baseGlyphScaleY * t.factor, 0);
                let spacingS = baselineSpacing;
                if (streamTokens.length > 1) {
                    const need = sumBaseS + (streamTokens.length - 1) * baselineSpacing;
                    spacingS = need <= availableHeight ? baselineSpacing + (availableHeight - need) / (streamTokens.length - 1) : 0;
                } else spacingS = 0;
                const totalS0 = sumBaseS + (streamTokens.length - 1) * spacingS;
                const addScaleS = totalS0 > availableHeight && sumBaseS > 0 ? Math.max(0.05, availableHeight / sumBaseS) : 1;
                const heightsS = streamTokens.map(t => (isParenSingle(t.ch) ? charHeight : charHeight * t.factor) * baseGlyphScaleY * addScaleS);
                let yDevS = yStartDevice;
                ctx.textAlign = align;
				for (let k = 0; k < streamTokens.length; k++) {
                    const t = streamTokens[k];
                    const h = heightsS[k];
                    const gY = (baseGlyphScaleY * (isParenSingle(t.ch) ? 1 : t.factor) * addScaleS);
                    const gX = baseGlyphScaleX * (isParenSingle(t.ch) ? 1 : t.factor); // bracket factor도 가로에 적용
                    ctx.save();
                    if (isParenSingle(t.ch)) {
						const baseChar = t.ch![1];
						ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
						const tokenWidth = ctx.measureText(t.ch!).width;
                        const tokenScaleX = Math.min(1, innerWidth / Math.max(1, tokenWidth));
                        ctx.scale(gX * tokenScaleX, gY);
						ctx.fillText(t.ch!, x / (gX * tokenScaleX), yDevS / gY);
                    } else {
						const baseChar = t.ch || ' ';
						ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
						ctx.scale(gX, gY);
						if (t.ch) ctx.fillText(t.ch, x / gX, yDevS / gY);
                    }
                    ctx.restore();
                    yDevS += h + spacingS;
                }
            };
            const innerW = Math.max(1, (targetInnerWidth / 2) - 4);
            const leftText = settings.content.slice(0, slashPos);
            const rightText = settings.content.slice(slashPos + 1);
            drawStream(leftText, ribbonX + sidePaddingPx, 'left', innerW);
            drawStream(rightText, ribbonX + ribbonWidthPx - sidePaddingPx, 'right', innerW);
            ctx.restore();
            return;
        }
        if (settings.verticalDirection === "bottom-up") {
            let yDev = yStartDevice;
            let idx = 0;
            for (const t of [...tokens].reverse()) {
                const h = tokenHeights[n - 1 - idx];
                let gY = (baseGlyphScaleY * t.factor * additionalScale);
                let gX = baseGlyphScaleX * t.factor; // bracket factor도 가로에 적용
                ctx.save();
					if (isParenSingle(t.ch)) {
                    gY = (baseGlyphScaleY * 1 * additionalScale);
                    gX = baseGlyphScaleX; // parenthesis는 bracket factor 적용 안함
						const baseChar = t.ch![1];
						ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
						const tokenWidth = ctx.measureText(t.ch!).width;
                    const innerWidth = t.col ? Math.max(1, (targetInnerWidth/2) - 4) : targetInnerWidth;
                    const tokenScaleX = Math.min(1, innerWidth / Math.max(1, tokenWidth));
                    const baseX = t.col === 'left' ? ribbonX + sidePaddingPx : t.col === 'right' ? ribbonX + ribbonWidthPx - sidePaddingPx : anchorX;
                    ctx.textAlign = t.col === 'left' ? 'left' : t.col === 'right' ? 'right' : ctx.textAlign;
                    ctx.scale(gX * tokenScaleX, gY);
                    ctx.fillText(t.ch!, baseX / (gX * tokenScaleX), yDev / gY);
                } else {
						const baseChar = t.ch || ' ';
						ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
						ctx.scale(gX, gY);
                    const baseX = t.col === 'left' ? ribbonX + sidePaddingPx : t.col === 'right' ? ribbonX + ribbonWidthPx - sidePaddingPx : anchorX;
                    ctx.textAlign = t.col === 'left' ? 'left' : t.col === 'right' ? 'right' : ctx.textAlign;
                    if (t.ch) ctx.fillText(t.ch, baseX / gX, yDev / gY);
                }
                ctx.restore();
                yDev += h + spacingDevice;
                idx++;
            }
        } else {
            let yDev = yStartDevice;
            let idx = 0;
            for (const t of tokens) {
                const h = tokenHeights[idx];
                let gY = (baseGlyphScaleY * t.factor * additionalScale);
                let gX = baseGlyphScaleX * t.factor; // bracket factor도 가로에 적용
                ctx.save();
					if (isParenSingle(t.ch)) {
                    gY = (baseGlyphScaleY * 1 * additionalScale);
                    gX = baseGlyphScaleX; // parenthesis는 bracket factor 적용 안함
						const baseChar = t.ch![1];
						ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
						const tokenWidth = ctx.measureText(t.ch!).width;
                    const innerWidth = t.col ? Math.max(1, (targetInnerWidth/2) - 4) : targetInnerWidth;
                    const tokenScaleX = Math.min(1, innerWidth / Math.max(1, tokenWidth));
                    const baseX = t.col === 'left' ? ribbonX + sidePaddingPx : t.col === 'right' ? ribbonX + ribbonWidthPx - sidePaddingPx : anchorX;
                    ctx.textAlign = t.col === 'left' ? 'left' : t.col === 'right' ? 'right' : ctx.textAlign;
                    ctx.scale(gX * tokenScaleX, gY);
                    ctx.fillText(t.ch!, baseX / (gX * tokenScaleX), yDev / gY);
                } else {
						const baseChar = t.ch || ' ';
						ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
						ctx.scale(gX, gY);
                    const baseX = t.col === 'left' ? ribbonX + sidePaddingPx : t.col === 'right' ? ribbonX + ribbonWidthPx - sidePaddingPx : anchorX;
                    ctx.textAlign = t.col === 'left' ? 'left' : t.col === 'right' ? 'right' : ctx.textAlign;
                    if (t.ch) ctx.fillText(t.ch, baseX / gX, yDev / gY);
                }
                ctx.restore();
                yDev += h + spacingDevice;
                idx++;
            }
        }
        ctx.restore();
	};

    useEffect(() => {
        drawRibbon(leftCanvasRef.current, leftSettings);
        drawRibbon(rightCanvasRef.current, rightSettings);
    }, [leftSettings, rightSettings, ribbonWidthPx, ribbonLengthPx, backgroundColor, fontKorean, fontCjk, fontLatin, baseFontFamily, baseFontSizePx, fontLoadTick]);

	const onLeftChange = <K extends keyof RibbonTextSettings>(key: K, value: RibbonTextSettings[K]) => {
		setLeftSettings((prev) => {
			const next = { ...prev, [key]: value } as RibbonTextSettings;
			// Do not propagate text content to the right side; only non-content settings follow applyBoth
			if (applyBoth && key !== 'content') {
				setRightSettings((r) => ({ ...r, [key]: value } as RibbonTextSettings));
			}
			return next;
		});
	};

	const handleDownload = (side: Side) => {
		const canvas = side === "left" ? leftCanvasRef.current : rightCanvasRef.current;
		if (!canvas) return;
		const url = applyCalibrationToDownload ? makeCalibratedDataUrl(canvas) : canvas.toDataURL("image/png");
		const a = document.createElement("a");
		a.href = url;
		a.download = `ribbon-${side}.png`;
		a.click();
	};

	const handlePrint = (side: Side) => {
		const canvas = side === "left" ? leftCanvasRef.current : rightCanvasRef.current;
		if (!canvas) return;
		const dataUrl = makeCalibratedDataUrl(canvas);
		const w = window.open("");
		if (!w) return;
		w.document.write(`<img src="${dataUrl}" style="width:100%" />`);
		w.document.close();
		w.focus();
		w.print();
	};

	const makeCalibratedDataUrl = (src: HTMLCanvasElement): string => {
		const scale = Math.max(0.1, printScalePercent / 100);
		const ox = mmToPx(printOffsetXmm);
		const oy = mmToPx(printOffsetYmm);
		const extraW = Math.abs(ox);
		const extraH = Math.abs(oy);
		const destW = Math.round(src.width * scale + extraW);
		const destH = Math.round(src.height * scale + extraH);
		const tmp = document.createElement("canvas");
		tmp.width = destW;
		tmp.height = destH;
		const ctx = tmp.getContext("2d");
		if (!ctx) return src.toDataURL("image/png");
		ctx.setTransform(scale, 0, 0, scale, Math.max(0, ox), Math.max(0, oy));
		ctx.drawImage(src, 0, 0);
		return tmp.toDataURL("image/png");
	};

    // Undo/Redo history support and file open/save
    type AppState = {
        ribbonWidthMm: number;
        ribbonLengthMm: number;
        backgroundColor: string;
        applyBoth: boolean;
        left: RibbonTextSettings;
        right: RibbonTextSettings;
    };
    const [history, setHistory] = useState<AppState[]>([]);
    const [historyIndex, setHistoryIndex] = useState<number>(-1);

    const snapshot = (): AppState => ({
        ribbonWidthMm, ribbonLengthMm, backgroundColor, applyBoth, left: leftSettings, right: rightSettings,
    });
    const applyState = (s: AppState) => {
        setRibbonWidthMm(s.ribbonWidthMm);
        setRibbonLengthMm(s.ribbonLengthMm);
        setBackgroundColor(s.backgroundColor);
        setApplyBoth(s.applyBoth);
        setLeftSettings(s.left);
        setRightSettings(s.right);
    };
    const pushHistory = () => {
        const snap = snapshot();
        const next = history.slice(0, historyIndex + 1);
        next.push(snap);
        setHistory(next);
        setHistoryIndex(next.length - 1);
    };
    const undo = () => {
        if (historyIndex <= 0) return;
        const idx = historyIndex - 1;
        setHistoryIndex(idx);
        applyState(history[idx]);
    };
    const redo = () => {
        if (historyIndex >= history.length - 1) return;
        const idx = historyIndex + 1;
        setHistoryIndex(idx);
        applyState(history[idx]);
    };
    useEffect(() => {
        if (historyIndex === -1) {
            const snap = snapshot();
            setHistory([snap]);
            setHistoryIndex(0);
        }
    }, []);
    useEffect(() => { pushHistory(); }, [ribbonWidthMm, ribbonLengthMm, backgroundColor, applyBoth, leftSettings, rightSettings]);
    
    // Auto-save environment when font settings change
    useEffect(() => {
        const env = {
            defaultPreset: envDefaultPreset,
            fontSource: envFontSource,
            systemFont: envSystemFont,
            webFontUrl: envWebFontUrl,
            webFontFamily: envWebFontFamily,
            webFonts: envWebFonts,
            webFontCssList: envWebFontCssList,
            printScale: envPrintScale,
            offsetXmm: envOffsetXmm,
            offsetYmm: envOffsetYmm,
            fontKorean,
            fontCjk,
            fontLatin,
        };
        localStorage.setItem("ribbonEnvV1", JSON.stringify(env));
    }, [envFontSource, envSystemFont, envWebFonts, envWebFontCssList, fontKorean, fontCjk, fontLatin, envDefaultPreset, envPrintScale, envOffsetXmm, envOffsetYmm]);
    // keep scale input mirrors in sync when state changes elsewhere
    useEffect(() => {
        setLeftScaleXStr(String(Math.round(leftSettings.scaleX * 100)));
        setLeftScaleYStr(String(Math.round(leftSettings.scaleY * 100)));
    }, [leftSettings.scaleX, leftSettings.scaleY]);
    useEffect(() => {
        setRightScaleXStr(String(Math.round(rightSettings.scaleX * 100)));
        setRightScaleYStr(String(Math.round(rightSettings.scaleY * 100)));
    }, [rightSettings.scaleX, rightSettings.scaleY]);

    const handleSaveJson = () => {
        const data = JSON.stringify(snapshot(), null, 2);
        const blob = new Blob([data], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "ribbon-editor.json";
        a.click();
        URL.revokeObjectURL(url);
    };
    const handleOpenClick = () => fileInputRef.current?.click();
    const handleOpenJson: React.ChangeEventHandler<HTMLInputElement> = async (e) => {
        const file = e.target.files?.[0];
        if (!file) return;
        const text = await file.text();
        const obj = JSON.parse(text) as AppState;
        applyState(obj);
    };
    const applyPreset = (key: string) => {
        const p = presets.find(p => p.key === key);
        if (!p) return;
        setSelectedPreset(key);
        setRibbonWidthMm(p.width);
        setRibbonLengthMm(p.length);
        // apply margins and ratios to both sides
        setLeftSettings(ls => ({
            ...ls,
            topMarginMm: p.topMm,
            bottomMarginMm: p.bottomMm,
            sidePaddingMm: p.laceMm,
            scaleX: Math.max(0.1, p.scaleXPercent / 100),
            scaleY: Math.max(0.1, p.scaleYPercent / 100),
            bracketScale: Math.max(0.05, p.bracketPercent / 100),
            applyBracketScale: ls.applyBracketScale,
        }));
        setRightSettings(rs => ({
            ...rs,
            topMarginMm: p.topMm,
            bottomMarginMm: p.bottomMm,
            sidePaddingMm: p.laceMm,
            scaleX: Math.max(0.1, p.scaleXPercent / 100),
            scaleY: Math.max(0.1, p.scaleYPercent / 100),
            bracketScale: Math.max(0.05, p.bracketPercent / 100),
            applyBracketScale: rs.applyBracketScale,
        }));
        setPrintOffsetXmm(p.startXmm);
        setPrintOffsetYmm(p.startYmm);
        // 미리보기 윗쪽 보조 안내선도 프리셋 참고값으로 동기화
        setGuide1Mm(p.topMm);
        setGuide2Mm(p.bottomMm);
    };

	// load environment on mount
	useEffect(() => {
        try {
			const raw = localStorage.getItem("ribbonEnvV1");
			if (raw) {
				const env = JSON.parse(raw);
				setEnvDefaultPreset(env.defaultPreset ?? envDefaultPreset);
                setEnvFontSource(env.fontSource ?? envFontSource);
                setEnvSystemFont(env.systemFont ?? envSystemFont);
                setEnvWebFontUrl(env.webFontUrl ?? envWebFontUrl); // legacy single
                setEnvWebFontFamily(env.webFontFamily ?? envWebFontFamily); // legacy single
                const wf: WebFontItem[] | undefined = env.webFonts;
                if (Array.isArray(wf) && wf.length > 0) {
                    setEnvWebFonts(wf);
                } else if ((env.webFontUrl ?? "") && (env.webFontFamily ?? "")) {
                    setEnvWebFonts([{ id: `wf-${Date.now()}`, url: env.webFontUrl, family: env.webFontFamily }]);
                } // Keep default initial values if no saved fonts
                const wfc: WebFontCssItem[] | undefined = env.webFontCssList;
                if (Array.isArray(wfc) && wfc.length > 0) setEnvWebFontCssList(wfc);
                // Keep default initial values if no saved CSS fonts
				setEnvPrintScale(env.printScale ?? envPrintScale);
				setEnvOffsetXmm(env.offsetXmm ?? envOffsetXmm);
				setEnvOffsetYmm(env.offsetYmm ?? envOffsetYmm);
				applyPreset(env.defaultPreset ?? envDefaultPreset);
                // apply font
                if ((env.fontSource ?? envFontSource) === "web") {
                    injectAllWebFonts(env.webFonts ?? envWebFonts);
                    injectCustomCssList(env.webFontCssList ?? envWebFontCssList);
                    const firstFamily = (env.webFonts && env.webFonts[0]?.family) || env.webFontFamily || baseFontFamily;
                    setBaseFontFamily(firstFamily);
                } else {
                    setBaseFontFamily(env.systemFont ?? baseFontFamily);
                }
                // load per-script fonts
                if (env.fontKorean) setFontKorean(env.fontKorean);
                if (env.fontCjk) setFontCjk(env.fontCjk);
                if (env.fontLatin) setFontLatin(env.fontLatin);
				setPrintScalePercent(env.printScale ?? printScalePercent);
				setPrintOffsetXmm(env.offsetXmm ?? printOffsetXmm);
				setPrintOffsetYmm(env.offsetYmm ?? printOffsetYmm);
			}
		} catch {}
	}, []);

    const saveEnvironment = () => {
        const env = {
			defaultPreset: envDefaultPreset,
            fontSource: envFontSource,
            systemFont: envSystemFont,
            webFontUrl: envWebFontUrl,
            webFontFamily: envWebFontFamily,
            webFonts: envWebFonts,
            webFontCssList: envWebFontCssList,
			printScale: envPrintScale,
			offsetXmm: envOffsetXmm,
			offsetYmm: envOffsetYmm,
            fontKorean,
            fontCjk,
            fontLatin,
		};
		localStorage.setItem("ribbonEnvV1", JSON.stringify(env));
		applyPreset(envDefaultPreset);
        if (envFontSource === "web") {
            injectAllWebFonts(envWebFonts);
            injectCustomCssList(envWebFontCssList);
            const firstFamily = envWebFonts[0]?.family || envWebFontFamily || baseFontFamily;
            setBaseFontFamily(firstFamily);
        } else {
            setBaseFontFamily(envSystemFont);
        }
        // No need to set per-script here; they are controlled by state above
        setPrintScalePercent(envPrintScale);
		setPrintOffsetXmm(envOffsetXmm);
		setPrintOffsetYmm(envOffsetYmm);
		setEnvOpen(false);
	};

    // Multi Ribbon Batch Functions
    const addRibbonToBatch = () => {
        const newId = (ribbonBatch.length + 1).toString();
        setRibbonBatch([...ribbonBatch, {
            id: newId,
            leftContent: leftSettings.content,
            rightContent: rightSettings.content,
            enabled: true
        }]);
    };
    
    const removeRibbonFromBatch = (id: string) => {
        setRibbonBatch(ribbonBatch.filter(r => r.id !== id));
    };
    
    const updateRibbonInBatch = (id: string, field: 'leftContent' | 'rightContent', value: string) => {
        setRibbonBatch(ribbonBatch.map(r => 
            r.id === id ? { ...r, [field]: value } : r
        ));
    };
    
    const toggleRibbonInBatch = (id: string) => {
        setRibbonBatch(ribbonBatch.map(r => 
            r.id === id ? { ...r, enabled: !r.enabled } : r
        ));
    };

    // Ribbon Print Functions
    const generateRibbonPrintLayout = () => {
        if (batchMode && isRollRibbon) {
            return generateBatchRibbonLayout();
        }
        
        // 단일 리본 출력
        return generateSingleRibbonLayout();
    };
    
    const generateSingleRibbonLayout = () => {
        // 현재 작업 중인 리본 크기 그대로 사용
        const ribbonWidth = ribbonWidthMm;
        // 롤 리본: 작업 길이 + 배출 여분, 재단 리본: 정확히 리본 길이만큼
        const printHeight = isRollRibbon 
            ? ribbonLengthMm + postFeed  // 롤리본: 작업 길이 + 배출 여분
            : ribbonLengthMm;            // 재단리본: 미리 잘라놓은 길이 그대로
        
        console.log('=== 리본 출력 디버깅 ===');
        console.log('Ribbon dimensions:', ribbonWidth + 'mm x ' + printHeight + 'mm');
        console.log('Print mode:', printMode);
        console.log('Left content:', leftSettings.content);
        console.log('Right content:', rightSettings.content);
        
        // Create print-specific canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('Canvas context creation failed');
            return null;
        }
        
        // Set canvas size (300 DPI for print quality)
        const dpi = 300;
        const mmToPx = (mm: number) => (mm * dpi) / 25.4;
        
        canvas.width = mmToPx(ribbonWidth);
        canvas.height = mmToPx(printHeight);
        
        console.log('Canvas pixel size:', canvas.width + 'px x ' + canvas.height + 'px');
        
        // Background
        ctx.fillStyle = backgroundColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        console.log('Background filled with:', backgroundColor);
        
        const centerX = canvas.width / 2;
        const leftZoneWidth = centerX - mmToPx(5); // 5mm margin from center
        const rightZoneWidth = centerX - mmToPx(5);
        
        console.log('Zones - Left width:', leftZoneWidth, 'Right width:', rightZoneWidth, 'Center X:', centerX);
        
        // Draw content based on print mode
        if (printMode === 'both' || printMode === 'left') {
            console.log('Drawing left content:', leftSettings.content);
            drawRibbonText(ctx, leftSettings, 0, leftZoneWidth, canvas.height, 'left', ribbonWidth);
        }
        
        if (printMode === 'both' && showCutLine) {
            console.log('Drawing cut line');
            // Center dividing line (중간구분선 인쇄 = 좌우 구분선)
            ctx.strokeStyle = '#000000';
            ctx.lineWidth = 2;
            ctx.setLineDash([10, 5]);
            ctx.beginPath();
            ctx.moveTo(centerX, 0);
            ctx.lineTo(centerX, canvas.height);
            ctx.stroke();
            ctx.setLineDash([]);
        }
        
        if (printMode === 'both' || printMode === 'right') {
            const rightStartX = printMode === 'both' ? centerX + mmToPx(5) : 0;
            const rightWidth = printMode === 'both' ? rightZoneWidth : canvas.width;
            console.log('Drawing right content:', rightSettings.content, 'at X:', rightStartX, 'width:', rightWidth);
            drawRibbonText(ctx, rightSettings, rightStartX, rightWidth, canvas.height, 'right', ribbonWidth);
        }
        
        // 롤리본 배출 영역 표시
        if (isRollRibbon && postFeed > 0) {
            const contentEndY = mmToPx(ribbonLengthMm);
            const feedAreaHeight = mmToPx(postFeed);
            
            // 배출 영역 배경 (연한 회색)
            ctx.fillStyle = '#f0f0f0';
            ctx.fillRect(0, contentEndY, canvas.width, feedAreaHeight);
            
            // 배출 영역 경계선
            ctx.strokeStyle = '#cccccc';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(0, contentEndY);
            ctx.lineTo(canvas.width, contentEndY);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // 배출 영역 라벨
            ctx.fillStyle = '#666666';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`배출 여분 ${postFeed}mm`, canvas.width / 2, contentEndY + feedAreaHeight / 2);
        }
        
        return canvas;
    };
    
    const generateBatchRibbonLayout = () => {
        const enabledRibbons = ribbonBatch.filter(r => r.enabled);
        if (enabledRibbons.length === 0) return null;
        
        const ribbonWidth = ribbonWidthMm;
        const singleRibbonHeight = ribbonLengthMm;
        const spacingHeight = ribbonSpacingMm;
        
        // 전체 배치 높이 계산: (리본 높이 × 개수) + (간격 × (개수-1)) + 배출 여분
        const totalBatchHeight = (singleRibbonHeight * enabledRibbons.length) + 
                                (spacingHeight * (enabledRibbons.length - 1)) + 
                                postFeed;
        
        // Create large batch canvas
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        if (!ctx) return null;
        
        // Set canvas size (300 DPI for print quality)
        const dpi = 300;
        const mmToPx = (mm: number) => (mm * dpi) / 25.4;
        
        canvas.width = mmToPx(ribbonWidth);
        canvas.height = mmToPx(totalBatchHeight);
        
        // Background
        ctx.fillStyle = backgroundColor;
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        
        // Draw each ribbon in sequence
        let currentY = 0;
        
        enabledRibbons.forEach((ribbon, index) => {
            const ribbonHeightPx = mmToPx(singleRibbonHeight);
            
            // Create temporary settings for this ribbon
            const tempLeftSettings = { ...leftSettings, content: ribbon.leftContent };
            const tempRightSettings = { ...rightSettings, content: ribbon.rightContent };
            
            const centerX = canvas.width / 2;
            const leftZoneWidth = centerX - mmToPx(5);
            const rightZoneWidth = centerX - mmToPx(5);
            
            // Draw content based on print mode
            if (printMode === 'both' || printMode === 'left') {
                drawRibbonTextAtPosition(ctx, tempLeftSettings, 0, leftZoneWidth, ribbonHeightPx, 'left', ribbonWidth, currentY);
            }
            
            if (printMode === 'both' && showCutLine) {
                // Center dividing line
                ctx.strokeStyle = '#000000';
                ctx.lineWidth = 2;
                ctx.setLineDash([10, 5]);
                ctx.beginPath();
                ctx.moveTo(centerX, currentY);
                ctx.lineTo(centerX, currentY + ribbonHeightPx);
                ctx.stroke();
                ctx.setLineDash([]);
            }
            
            if (printMode === 'both' || printMode === 'right') {
                const rightStartX = printMode === 'both' ? centerX + mmToPx(5) : 0;
                const rightWidth = printMode === 'both' ? rightZoneWidth : canvas.width;
                drawRibbonTextAtPosition(ctx, tempRightSettings, rightStartX, rightWidth, ribbonHeightPx, 'right', ribbonWidth, currentY);
            }
            
            // Add ribbon number label (optional)
            if (enabledRibbons.length > 1) {
                ctx.fillStyle = '#cccccc';
                ctx.font = '8px Arial';
                ctx.textAlign = 'right';
                ctx.fillText(`#${ribbon.id}`, canvas.width - 5, currentY + 15);
            }
            
            currentY += ribbonHeightPx;
            
            // Add spacing between ribbons (except after last ribbon)
            if (index < enabledRibbons.length - 1) {
                // Draw spacing area with light background
                const spacingHeightPx = mmToPx(spacingHeight);
                ctx.fillStyle = '#f8f8f8';
                ctx.fillRect(0, currentY, canvas.width, spacingHeightPx);
                
                // Draw separator line
                ctx.strokeStyle = '#e0e0e0';
                ctx.lineWidth = 1;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(0, currentY + spacingHeightPx / 2);
                ctx.lineTo(canvas.width, currentY + spacingHeightPx / 2);
                ctx.stroke();
                ctx.setLineDash([]);
                
                currentY += spacingHeightPx;
            }
        });
        
        // 롤리본 배출 영역 표시
        if (postFeed > 0) {
            const feedAreaHeight = mmToPx(postFeed);
            
            // 배출 영역 배경 (연한 회색)
            ctx.fillStyle = '#f0f0f0';
            ctx.fillRect(0, currentY, canvas.width, feedAreaHeight);
            
            // 배출 영역 경계선
            ctx.strokeStyle = '#cccccc';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.beginPath();
            ctx.moveTo(0, currentY);
            ctx.lineTo(canvas.width, currentY);
            ctx.stroke();
            ctx.setLineDash([]);
            
            // 배출 영역 라벨
            ctx.fillStyle = '#666666';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`배출 여분 ${postFeed}mm`, canvas.width / 2, currentY + feedAreaHeight / 2);
        }
        
        return canvas;
    };
    
    const drawRibbonTextAtPosition = (
        ctx: CanvasRenderingContext2D, 
        settings: RibbonTextSettings, 
        startX: number, 
        width: number, 
        height: number, 
        side: 'left' | 'right',
        ribbonWidthMm: number,
        offsetY: number = 0
    ) => {
        ctx.save();
        ctx.translate(0, offsetY);
        drawRibbonText(ctx, settings, startX, width, height, side, ribbonWidthMm);
        ctx.restore();
    };

    const drawRibbonText = (
        ctx: CanvasRenderingContext2D, 
        settings: RibbonTextSettings, 
        startX: number, 
        width: number, 
        height: number, 
        side: 'left' | 'right',
        ribbonWidthMm: number
    ) => {
        const content = settings.content;
        if (!content || !content.trim()) return;
        
        // Print DPI scaling factor (300 DPI vs 96 DPI screen)
        const dpiScale = 300 / 96;
        
        // 폰트 설정
        const usedFontSize = Math.floor(settings.fontSizePx * dpiScale);
        const fontWeight = settings.isBold ? '700' : '400';
        const fontStyle = settings.isItalic ? 'italic' : 'normal';
        
        // Helper functions from preview
        const fontChainForChar = (char: string) => {
            const code = char.charCodeAt(0);
            if ((code >= 0x1100 && code <= 0x11FF) || 
                (code >= 0x3130 && code <= 0x318F) || 
                (code >= 0xAC00 && code <= 0xD7AF)) {
                return `"${settings.koreanFont || fontKorean}", "${settings.cjkFont || fontCjk}", "${settings.latinFont || fontLatin}", ${baseFontFamily}, sans-serif`;
            }
            if ((code >= 0x4E00 && code <= 0x9FFF) || 
                (code >= 0x3400 && code <= 0x4DBF)) {
                return `"${settings.cjkFont || fontCjk}", "${settings.koreanFont || fontKorean}", "${settings.latinFont || fontLatin}", ${baseFontFamily}, sans-serif`;
            }
            return `"${settings.latinFont || fontLatin}", "${settings.koreanFont || fontKorean}", "${settings.cjkFont || fontCjk}", ${baseFontFamily}, sans-serif`;
        };
        
        const isParenSingle = (text: string) => {
            return text && text.length >= 3 && text[0] === '(' && text[text.length - 1] === ')';
        };
        
        ctx.save();
        ctx.fillStyle = settings.color;
        
        // Scale all measurements
        const ribbonWidthPx = width;
        const ribbonHeightPx = height;
        const sidePaddingPx = settings.sidePaddingMm * dpiScale * 3.7795275591;
        const topMarginPx = settings.topMarginMm * dpiScale * 3.7795275591;
        const bottomMarginPx = settings.bottomMarginMm * dpiScale * 3.7795275591;
        const charSpacingPx = settings.charSpacingMm * dpiScale * 3.7795275591;
        
        const ribbonX = startX;
        const ribbonY = 0;
        
        // Calculate available area
        const availableHeight = ribbonHeightPx - topMarginPx - bottomMarginPx;
        const targetInnerWidth = ribbonWidthPx - 2 * sidePaddingPx;
        
        // Split content by newlines
        const lines = content.split('\n').filter(line => line.trim());
        
        // For print mode direction handling
        let processedLines = [...lines];
        if (printMode === 'both') {
            if (side === 'left') {
                // Left side: reverse order (bottom to top) for folding alignment
                processedLines = [...lines].reverse();
            }
            // Right side: keep normal order (top to bottom)
        }
        
        // Process each line
        const lineHeight = usedFontSize * 1.2;
        const totalTextHeight = processedLines.length * lineHeight;
        const yStartDevice = ribbonY + topMarginPx + (availableHeight - totalTextHeight) / 2;
        
        let currentY = yStartDevice;
        
        for (const line of processedLines) {
            if (!line.trim()) {
                currentY += lineHeight;
                continue;
            }
            
            // Check for two-column layout (/) 
            const slashPos = line.indexOf('/');
            
            if (slashPos >= 0) {
                // Two-column layout
                const drawStream = (text: string, x: number, align: CanvasTextAlign, innerWidth: number) => {
                    const streamTokens: { ch: string; factor: number }[] = [];
                    let i = 0;
                    while (i < text.length) {
                        if (text[i] === '[') {
                            const closeIndex = text.indexOf(']', i);
                            if (closeIndex > i) {
                                const bracketContent = text.slice(i + 1, closeIndex);
                                for (const ch of bracketContent) {
                                    streamTokens.push({ ch, factor: settings.bracketScale || 0.5 });
                                }
                                i = closeIndex + 1;
                            } else {
                                streamTokens.push({ ch: text[i], factor: 1 });
                                i++;
                            }
                        } else {
                            streamTokens.push({ ch: text[i], factor: 1 });
                            i++;
                        }
                    }
                    
                    if (streamTokens.length === 0) return;
                    
                    // Calculate scaling
                    const baseGlyphScaleX = settings.scaleX;
                    const baseGlyphScaleY = settings.scaleY;
                    const charHeight = usedFontSize;
                    const spacingS = charSpacingPx;
                    
                    const sumBaseS = streamTokens.reduce((sum, t) => {
                        return sum + (isParenSingle(t.ch) ? charHeight : charHeight * t.factor);
                    }, 0);
                    const totalS0 = sumBaseS + (streamTokens.length - 1) * spacingS;
                    const addScaleS = totalS0 > availableHeight && sumBaseS > 0 ? Math.max(0.05, availableHeight / sumBaseS) : 1;
                    
                    const heightsS = streamTokens.map(t => (isParenSingle(t.ch) ? charHeight : charHeight * t.factor) * baseGlyphScaleY * addScaleS);
                    let yDevS = currentY;
                    
                    ctx.textAlign = align;
                    
                    for (let k = 0; k < streamTokens.length; k++) {
                        const t = streamTokens[k];
                        const h = heightsS[k];
                        const gY = (baseGlyphScaleY * (isParenSingle(t.ch) ? 1 : t.factor) * addScaleS);
                        const gX = baseGlyphScaleX * (isParenSingle(t.ch) ? 1 : t.factor);
                        
                        ctx.save();
                        if (isParenSingle(t.ch)) {
                            const baseChar = t.ch[1];
                            ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
                            const tokenWidth = ctx.measureText(t.ch).width;
                            const tokenScaleX = Math.min(1, innerWidth / Math.max(1, tokenWidth));
                            ctx.scale(gX * tokenScaleX, gY);
                            ctx.fillText(t.ch, x / (gX * tokenScaleX), yDevS / gY);
                        } else {
                            const baseChar = t.ch || ' ';
                            ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
                            ctx.scale(gX, gY);
                            if (t.ch) ctx.fillText(t.ch, x / gX, yDevS / gY);
                        }
                        ctx.restore();
                        yDevS += h + spacingS;
                    }
                };
                
                const innerW = Math.max(1, (targetInnerWidth / 2) - 4);
                const leftText = line.slice(0, slashPos);
                const rightText = line.slice(slashPos + 1);
                drawStream(leftText, ribbonX + sidePaddingPx, 'left', innerW);
                drawStream(rightText, ribbonX + ribbonWidthPx - sidePaddingPx, 'right', innerW);
            } else {
                // Single-column layout - process with bracket scaling
                const tokens: { ch: string; factor: number }[] = [];
                let i = 0;
                while (i < line.length) {
                    if (line[i] === '[') {
                        const closeIndex = line.indexOf(']', i);
                        if (closeIndex > i) {
                            const bracketContent = line.slice(i + 1, closeIndex);
                            for (const ch of bracketContent) {
                                tokens.push({ ch, factor: settings.bracketScale || 0.5 });
                            }
                            i = closeIndex + 1;
                        } else {
                            tokens.push({ ch: line[i], factor: 1 });
                            i++;
                        }
                    } else {
                        tokens.push({ ch: line[i], factor: 1 });
                        i++;
                    }
                }
                
                if (tokens.length > 0) {
                    // Calculate scaling
                    const baseGlyphScaleX = settings.scaleX;
                    const baseGlyphScaleY = settings.scaleY;
                    const charHeight = usedFontSize;
                    const spacingS = charSpacingPx;
                    
                    const sumBaseS = tokens.reduce((sum, t) => {
                        return sum + (isParenSingle(t.ch) ? charHeight : charHeight * t.factor);
                    }, 0);
                    const totalS0 = sumBaseS + (tokens.length - 1) * spacingS;
                    const addScaleS = totalS0 > availableHeight && sumBaseS > 0 ? Math.max(0.05, availableHeight / sumBaseS) : 1;
                    
                    const heightsS = tokens.map(t => (isParenSingle(t.ch) ? charHeight : charHeight * t.factor) * baseGlyphScaleY * addScaleS);
                    let yDevS = currentY;
                    
                    ctx.textAlign = settings.horizontalAlign === 'left' ? 'left' : 
                                   settings.horizontalAlign === 'right' ? 'right' : 'center';
                    
                    const alignX = settings.horizontalAlign === 'left' ? ribbonX + sidePaddingPx :
                                  settings.horizontalAlign === 'right' ? ribbonX + ribbonWidthPx - sidePaddingPx :
                                  ribbonX + ribbonWidthPx / 2;
                    
                    for (let k = 0; k < tokens.length; k++) {
                        const t = tokens[k];
                        const h = heightsS[k];
                        const gY = (baseGlyphScaleY * (isParenSingle(t.ch) ? 1 : t.factor) * addScaleS);
                        const gX = baseGlyphScaleX * (isParenSingle(t.ch) ? 1 : t.factor);
                        
                        ctx.save();
                        if (isParenSingle(t.ch)) {
                            const baseChar = t.ch[1];
                            ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
                            const tokenWidth = ctx.measureText(t.ch).width;
                            const tokenScaleX = Math.min(1, targetInnerWidth / Math.max(1, tokenWidth));
                            ctx.scale(gX * tokenScaleX, gY);
                            ctx.fillText(t.ch, alignX / (gX * tokenScaleX), yDevS / gY);
                        } else {
                            const baseChar = t.ch || ' ';
                            ctx.font = `${fontStyle} ${fontWeight} ${usedFontSize}px ${fontChainForChar(baseChar)}`;
                            ctx.scale(gX, gY);
                            if (t.ch) ctx.fillText(t.ch, alignX / gX, yDevS / gY);
                        }
                        ctx.restore();
                        yDevS += h + spacingS;
                    }
                }
            }
            
            currentY += lineHeight;
        }
        
        ctx.restore();
    };
    
    const executeRibbonPrint = () => {
        const canvas = generateRibbonPrintLayout();
        if (!canvas) {
            alert('캔버스 생성에 실패했습니다.');
            return;
        }
        
        // 디버깅: 캔버스 크기 확인
        console.log('Canvas size:', canvas.width, 'x', canvas.height);
        
        const ribbonWidth = ribbonWidthMm;
        const printHeight = isRollRibbon 
            ? ribbonLengthMm + postFeed  // 롤리본: 작업 길이 + 배출 여분
            : ribbonLengthMm;            // 재단리본: 미리 잘라놓은 길이 그대로
        
        // 캔버스를 이미지로 변환 (고품질)
        const dataURL = canvas.toDataURL('image/png', 1.0);
        
        // 디버깅: 이미지 데이터 확인
        console.log('DataURL length:', dataURL.length);
        console.log('DataURL preview:', dataURL.substring(0, 100));
        
        // Create print window with enhanced settings
        const printWindow = window.open('', '_blank', 'width=800,height=600');
        if (!printWindow) {
            alert('팝업이 차단되었습니다. 팝업을 허용해주세요.');
            return;
        }
        
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>리본 프린트 - ${selectedPrinter}</title>
                <style>
                    @page {
                        size: ${ribbonWidth}mm ${isRollRibbon ? 'auto' : printHeight + 'mm'};
                        margin: 0mm;
                        padding: 0mm;
                        ${isRollRibbon ? `
                        /* 롤 리본: 연속 배너 모드 */
                        -webkit-print-color-adjust: exact;
                        print-color-adjust: exact;
                        ` : ''}
                    }
                    * {
                        margin: 0;
                        padding: 0;
                        box-sizing: border-box;
                    }
                    html, body {
                        width: 100%;
                        height: 100%;
                        overflow: hidden;
                    }
                    .print-container {
                        width: ${ribbonWidth}mm;
                        ${isRollRibbon ? `
                        min-height: ${printHeight}mm;
                        height: auto;
                        ` : `height: ${printHeight}mm;`}
                        margin: 0;
                        padding: 0;
                        display: block;
                        position: relative;
                        ${isRollRibbon ? `
                        /* 롤 리본: 연속 출력 설정 */
                        page-break-inside: avoid;
                        break-inside: avoid;
                        ` : ''}
                    }
                    .ribbon-image {
                        width: 100%;
                        height: 100%;
                        object-fit: contain;
                        image-rendering: -webkit-optimize-contrast;
                        image-rendering: crisp-edges;
                        image-rendering: pixelated;
                        display: block;
                    }
                    @media print {
                        html, body {
                            width: ${ribbonWidth}mm !important;
                            ${isRollRibbon ? `
                            height: auto !important;
                            min-height: ${printHeight}mm !important;
                            ` : `height: ${printHeight}mm !important;`}
                        }
                        .print-container {
                            ${isRollRibbon ? `
                            /* 롤 리본: 연속 배너 출력 */
                            page-break-inside: avoid;
                            break-inside: avoid;
                            ` : `
                            /* 재단 리본: 단일 페이지 출력 */
                            break-inside: avoid;
                            page-break-inside: avoid;
                            page-break-before: avoid;
                            page-break-after: avoid;
                            `}
                        }
                        .ribbon-image {
                            break-inside: avoid;
                            ${isRollRibbon ? `
                            height: auto !important;
                            min-height: ${printHeight}mm;
                            ` : ''}
                        }
                        ${isRollRibbon ? `
                        /* 롤 리본 전용 스타일 */
                        @page :first {
                            margin-top: 0mm;
                        }
                        @page :last {
                            margin-bottom: ${postFeed}mm;
                        }
                        ` : ''}
                    }
                    @media screen {
                        body {
                            background: #f0f0f0;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            min-height: 100vh;
                        }
                        .print-container {
                            background: white;
                            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                            border: 1px solid #ddd;
                        }
                        .print-info {
                            position: fixed;
                            top: 10px;
                            left: 10px;
                            background: rgba(0,0,0,0.8);
                            color: white;
                            padding: 10px;
                            border-radius: 4px;
                            font-family: Arial, sans-serif;
                            font-size: 12px;
                        }
                    }
                </style>
                <script>
                    let imageLoaded = false;
                    
                    function checkAndPrint() {
                        if (imageLoaded) {
                            console.log('Image loaded, starting print...');
                            setTimeout(function() {
                                window.print();
                            }, 500);
                        }
                    }
                    
                    window.addEventListener('load', function() {
                        console.log('Window loaded');
                        const img = document.querySelector('.ribbon-image');
                        if (img) {
                            if (img.complete) {
                                console.log('Image already loaded');
                                imageLoaded = true;
                                checkAndPrint();
                            } else {
                                img.onload = function() {
                                    console.log('Image loaded successfully');
                                    imageLoaded = true;
                                    checkAndPrint();
                                };
                                img.onerror = function() {
                                    console.error('Image failed to load');
                                    alert('이미지 로드에 실패했습니다.');
                                };
                            }
                        }
                    });
                    
                    window.addEventListener('afterprint', function() {
                        console.log('Print completed');
                        setTimeout(function() {
                            window.close();
                        }, 500);
                    });
                </script>
            </head>
            <body>
                <div class="print-info">
                    프린터: ${selectedPrinter}<br>
                    크기: ${ribbonWidth}mm × ${printHeight}mm<br>
                    모드: ${printMode === 'both' ? '양쪽' : printMode === 'left' ? '좌측' : '우측'}<br>
                    리본: ${isRollRibbon ? '롤' : '재단'}${isRollRibbon ? ` (배출: ${postFeed}mm)` : ''}<br>
                    배치모드: ${batchMode ? `ON (${ribbonBatch.filter(r => r.enabled).length}개 리본)` : 'OFF'}
                </div>
                <div class="print-container">
                    <img class="ribbon-image" src="${dataURL}" alt="Ribbon Print" onload="console.log('IMG onload triggered')" onerror="console.error('IMG onerror triggered')" />
                </div>
            </body>
            </html>
        `);
        
        printWindow.document.close();
        setPrintDialogOpen(false);
    };

    const clearInjectedWebFonts = () => {
        const legacy = document.getElementById('dynamic-webfont-link');
        if (legacy) legacy.remove();
        const nodes = Array.from(document.querySelectorAll('link[id^="dynamic-webfont-link-"], style[id^="dynamic-webfont-face-"]'));
        nodes.forEach(n => n.parentElement?.removeChild(n));
    };
    const injectWebFont = (url: string, idSuffix: string) => {
        const id = `dynamic-webfont-link-${idSuffix}`;
        let el = document.getElementById(id) as HTMLLinkElement | null;
        if (!el) {
            el = document.createElement('link');
            el.id = id;
            el.rel = 'stylesheet';
            document.head.appendChild(el);
        }
        el.href = url;
    };
    const injectFaceFont = (family: string, url: string, idSuffix: string) => {
        const id = `dynamic-webfont-face-${idSuffix}`;
        let el = document.getElementById(id) as HTMLStyleElement | null;
        if (!el) {
            el = document.createElement('style');
            el.id = id;
            document.head.appendChild(el);
        }
        const safeFamily = family.replace(/"/g, '\\"');
        el.textContent = `@font-face{font-family:"${safeFamily}";src:url("${url}") format("${url.endsWith('.otf') ? 'opentype' : url.endsWith('.ttf') ? 'truetype' : url.endsWith('.woff2') ? 'woff2' : 'woff'}");font-weight:normal;font-style:normal;font-display:swap;}`;
    };
    const injectAllWebFonts = (items: WebFontItem[] = []) => {
        clearInjectedWebFonts();
        items.forEach((it, idx) => {
            const u = it.url || '';
            if (/\.(woff2?|ttf|otf)(\?|$)/i.test(u)) injectFaceFont(it.family, u, String(idx));
            else injectWebFont(u, String(idx));
        });
        try {
            const navFonts = (document as { fonts?: { load?: (font: string) => Promise<FontFace[]> } }).fonts;
            if (navFonts && navFonts.load) {
                Promise.all(items.map(it => navFonts.load!(`16px "${it.family}"`))).then(() => {
                    setFontLoadTick(t => t + 1);
                }).catch(() => setFontLoadTick(t => t + 1));
            } else {
                setFontLoadTick(t => t + 1);
            }
        } catch { setFontLoadTick(t => t + 1); }
    };
    const injectCustomCssList = (items: WebFontCssItem[] = []) => {
        items.forEach((it, idx) => {
            const id = `dynamic-webfont-css-${idx}`;
            let el = document.getElementById(id) as HTMLStyleElement | null;
            if (!el) { el = document.createElement('style'); el.id = id; document.head.appendChild(el); }
            el.textContent = it.css;
        });
        setFontLoadTick(t => t + 1);
    };

  return (
		<div className="min-h-screen bg-white text-gray-900">
			<header className="sticky top-0 z-10 border-b border-gray-200 bg-white/85 backdrop-blur">
				<div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
                    <h1 className="text-lg font-semibold">리본 인쇄 에디터 (웹)</h1>
                    <div className="flex items-center gap-2 text-sm">
                        <button onClick={() => { setLeftSettings({ ...leftSettings, content: "" }); setRightSettings({ ...rightSettings, content: "" }); }} className="px-3 py-1.5 btn-blue"><PlusCircle className="w-4 h-4 inline mr-1"/>새리본</button>
                        <button onClick={handleOpenClick} className="px-3 py-1.5 btn-blue"><FolderOpen className="w-4 h-4 inline mr-1"/>파일열기</button>
                        <button onClick={handleSaveJson} className="px-3 py-1.5 btn-blue"><Save className="w-4 h-4 inline mr-1"/>저장</button>
                        <button onClick={undo} className="px-2 py-1.5 input-bevel"><Undo2 className="w-4 h-4"/></button>
                        <button onClick={redo} className="px-2 py-1.5 input-bevel"><Redo2 className="w-4 h-4"/></button>
                        <button onClick={() => { window.open("#help", "_blank"); }} className="px-2 py-1.5 input-bevel"><HelpCircle className="w-4 h-4"/></button>
                        <button onClick={() => setEnvOpen(true)} className="px-3 py-1.5 input-bevel"><Settings className="w-4 h-4 inline mr-1"/>환경설정</button>
                        <label className="inline-flex items-center gap-2 ml-3"><input type="checkbox" checked={applyBoth} onChange={(e) => setApplyBoth(e.target.checked)} /> 동시적용</label>
                                <div className="flex items-center gap-2 ml-3">
                            <span className="text-gray-600">배율</span>
                                    <input type="range" min={0.2} max={1} step={0.1} value={scale} onChange={(e) => setScale(Number(e.target.value))} disabled={fitBoth} />
                                    <label className="inline-flex items-center gap-1 text-xs text-gray-600">
                                        <input type="checkbox" checked={fitBoth} onChange={(e)=>setFitBoth(e.target.checked)} /> 두줄 자동 맞춤
                                    </label>
                                    {fitBoth && <span className="text-xs text-gray-500">x{effectiveScale.toFixed(2)}</span>}
                        </div>
                    </div>
				</div>
			</header>

			<div className="max-w-7xl mx-auto p-4 grid grid-cols-1 lg:grid-cols-3 gap-4">
                <section ref={leftPanelRef} className="lg:col-span-1 panel rounded-lg p-4">
					<h2 className="font-medium mb-3">설정</h2>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
						<div className="flex items-center gap-1">
							<button type="button" onClick={() => {
								const idx = presets.findIndex(p => p.key === selectedPreset);
								const nextIdx = (idx - 1 + presets.length) % presets.length;
								applyPreset(presets[nextIdx].key);
							}} className="rounded-md border px-2 py-2 text-xs"><ChevronLeft className="w-4 h-4"/></button>
                                <select value={selectedPreset} onChange={(e) => applyPreset(e.target.value)} className="input-bevel px-3 py-2 text-sm min-w-[220px]">
                                    {presets.map(p => (
                                        <option key={p.key} value={p.key}>{getPresetDisplayLabel(p)}</option>
                                    ))}
							</select>
							<button type="button" onClick={() => {
								const idx = presets.findIndex(p => p.key === selectedPreset);
								const nextIdx = (idx + 1) % presets.length;
								applyPreset(presets[nextIdx].key);
							}} className="rounded-md border px-2 py-2 text-xs"><ChevronRight className="w-4 h-4"/></button>
                                <button type="button" onClick={() => setPresetOpen(true)} className="rounded-md border px-2 py-2 text-xs ml-2">리본 목록 편집</button>
						</div>
                            <label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={applyBoth} onChange={(e) => setApplyBoth(e.target.checked)} /> 동시적용</label>
                        </div>
						<div className="grid grid-cols-2 gap-3">
                            <label className="block col-span-1">
								<span className="block text-sm text-gray-600">리본 폭(mm)</span>
                                <input type="number" value={ribbonWidthMm} onChange={(e) => setRibbonWidthMm(Number(e.target.value) || 1)} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={10} max={200} />
							</label>
                            <label className="block col-span-1">
								<span className="block text-sm text-gray-600">리본 길이(mm)</span>
                                <input type="number" value={ribbonLengthMm} onChange={(e) => setRibbonLengthMm(Number(e.target.value) || 1)} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={50} max={5000} />
							</label>
						</div>

                        <div className="panel rounded-md p-3">
							<div className="font-medium text-sm mb-2">좌측: {leftSettings.label}</div>
                            <div className="grid grid-cols-3 gap-2 mb-2">
                                <select value={leftSampleCat} onChange={(e) => setLeftSampleCat(e.target.value)} className="input-bevel px-2 py-2 text-sm">
                                    {samples.map(c => <option key={c.key} value={c.key}>{c.name}</option>)}
                                </select>
                                <select onChange={(e) => { const cat = samples.find(c => c.key === leftSampleCat); const item = cat?.items.find(i => i.label === e.target.value); if (item) setLeftSettings(p => ({ ...p, content: preferHanjaFromLabel(item.label, item.value) })); }} className="col-span-2 input-bevel px-2 py-2 text-sm">
                                    {(samples.find(c => c.key === leftSampleCat)?.items ?? []).map(it => <option key={it.label} value={it.label}>{it.label}</option>)}
                                </select>
                            </div>
							<label className="block mb-2">
								<span className="block text-sm text-gray-600">텍스트</span>
								<input value={leftSettings.content} onChange={(e) => onLeftChange("content", e.target.value)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" />
							</label>
                            {/* 개별 폰트/크기 설정 제거됨 (전역 폰트 설정 사용) */}
							<div className="grid grid-cols-3 gap-3 mt-2">
								<label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={leftSettings.isBold} onChange={(e) => onLeftChange("isBold", e.target.checked)} /> Bold</label>
								<label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={leftSettings.isItalic} onChange={(e) => onLeftChange("isItalic", e.target.checked)} /> Italic</label>
								<label className="block">
									<span className="block text-sm text-gray-600">텍스트 색</span>
                                    <input type="color" value={leftSettings.color} onChange={(e) => onLeftChange("color", e.target.value)} className="mt-1 h-9 w-full input-bevel px-2" />
								</label>
							</div>
                            <div className="grid grid-cols-3 gap-3 mt-2">
								<label className="block">
									<span className="block text-sm text-gray-600">문자 간격(mm)</span>
                                    <input type="number" value={leftSettings.charSpacingMm} onChange={(e) => onLeftChange("charSpacingMm", Number(e.target.value) || 0)} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={0} max={50} />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">상단 여백(mm)</span>
                                    <input type="number" value={leftSettings.topMarginMm} onChange={(e) => onLeftChange("topMarginMm", Number(e.target.value) || 0)} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={0} max={200} />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">하단 여백(mm)</span>
                                    <input type="number" value={leftSettings.bottomMarginMm} onChange={(e) => onLeftChange("bottomMarginMm", Number(e.target.value) || 0)} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={0} max={200} />
								</label>
                                <label className="block">
                                    <span className="block text-sm text-gray-600">가로 비율(%)</span>
                                    <input type="text" inputMode="numeric" pattern="[0-9]*" value={leftScaleXStr} onChange={(e) => {
                                        const v = e.target.value;
                                        if (/^\d{0,3}$/.test(v)) setLeftScaleXStr(v);
                                    }} onBlur={() => {
                                        const n = Number(leftScaleXStr);
                                        const clamped = isNaN(n) ? Math.round(leftSettings.scaleX * 100) : Math.max(10, Math.min(300, n));
                                        setLeftScaleXStr(String(clamped));
                                        onLeftChange("scaleX", clamped / 100);
                                    }} className="mt-1 w-full input-bevel px-3 py-2 text-sm" />
                                </label>
                                <label className="block">
                                    <span className="block text-sm text-gray-600">세로 비율(%)</span>
                                    <input type="text" inputMode="numeric" pattern="[0-9]*" value={leftScaleYStr} onChange={(e) => {
                                        const v = e.target.value;
                                        if (/^\d{0,3}$/.test(v)) setLeftScaleYStr(v);
                                    }} onBlur={() => {
                                        const n = Number(leftScaleYStr);
                                        const clamped = isNaN(n) ? Math.round(leftSettings.scaleY * 100) : Math.max(10, Math.min(300, n));
                                        setLeftScaleYStr(String(clamped));
                                        onLeftChange("scaleY", clamped / 100);
                                    }} className="mt-1 w-full input-bevel px-3 py-2 text-sm" />
                                </label>
							<label className="block">
								<span className="block text-sm text-gray-600">가로 정렬</span>
                                    <select value={leftSettings.horizontalAlign} onChange={(e) => onLeftChange("horizontalAlign", e.target.value as "left" | "center" | "right")} className="mt-1 w-full input-bevel px-3 py-2 text-sm">
									<option value="left">왼쪽</option>
									<option value="center">가운데</option>
									<option value="right">오른쪽</option>
								</select>
							</label>
							<label className="block">
								<span className="block text-sm text-gray-600">세로 방향</span>
                                    <select value={leftSettings.verticalDirection} onChange={(e) => onLeftChange("verticalDirection", e.target.value as "top-down" | "bottom-up")} className="mt-1 w-full input-bevel px-3 py-2 text-sm">
									<option value="top-down">위→아래</option>
									<option value="bottom-up">아래→위</option>
								</select>
							</label>
								<label className="inline-flex items-center gap-2 text-sm col-span-3"><input type="checkbox" checked={leftSettings.autoFit} onChange={(e) => onLeftChange("autoFit", e.target.checked)} /> 리본 폭에 맞게 자동 폰트 크기</label>
								<label className="block col-span-3">
									<span className="block text-sm text-gray-600">양옆 여백(mm)</span>
									<input type="number" value={leftSettings.sidePaddingMm} onChange={(e) => onLeftChange("sidePaddingMm", Number(e.target.value) || 0)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" min={0} max={20} />
								</label>
							</div>
						</div>

                        <div className="panel rounded-md p-3">
							<div className="font-medium text-sm mb-2">우측: {rightSettings.label}</div>
                            <div className="grid grid-cols-3 gap-2 mb-2">
                                <select value={rightSenderCat} onChange={(e) => setRightSenderCat(e.target.value)} className="input-bevel px-2 py-2 text-sm">
                                    {senderSamples.map(c => <option key={c.key} value={c.key}>{c.name}</option>)}
                                </select>
                                <select onChange={(e) => { const cat = senderSamples.find(c => c.key === rightSenderCat); const item = cat?.items.find(i => i.label === e.target.value); if (item) setRightSettings(p => ({ ...p, content: item.value })); }} className="col-span-2 input-bevel px-2 py-2 text-sm">
                                    {(senderSamples.find(c => c.key === rightSenderCat)?.items ?? []).map(it => <option key={it.label} value={it.label}>{it.label}</option>)}
                                </select>
                            </div>
							<label className="block mb-2">
								<span className="block text-sm text-gray-600">텍스트</span>
								<input value={rightSettings.content} onChange={(e) => setRightSettings((p) => ({ ...p, content: e.target.value }))} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" />
							</label>
                            {/* 개별 폰트/크기 설정 제거됨 (전역 폰트 설정 사용) */}
							<div className="grid grid-cols-3 gap-3 mt-2">
								<label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={rightSettings.isBold} onChange={(e) => setRightSettings((p) => ({ ...p, isBold: e.target.checked }))} /> Bold</label>
								<label className="inline-flex items-center gap-2 text-sm"><input type="checkbox" checked={rightSettings.isItalic} onChange={(e) => setRightSettings((p) => ({ ...p, isItalic: e.target.checked }))} /> Italic</label>
								<label className="block">
									<span className="block text-sm text-gray-600">텍스트 색</span>
                                    <input type="color" value={rightSettings.color} onChange={(e) => setRightSettings((p) => ({ ...p, color: e.target.value }))} className="mt-1 h-9 w-full input-bevel px-2" />
								</label>
							</div>
                            <div className="grid grid-cols-3 gap-3 mt-2">
								<label className="block">
									<span className="block text-sm text-gray-600">문자 간격(mm)</span>
                                    <input type="number" value={rightSettings.charSpacingMm} onChange={(e) => setRightSettings((p) => ({ ...p, charSpacingMm: Number(e.target.value) || 0 }))} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={0} max={50} />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">상단 여백(mm)</span>
                                    <input type="number" value={rightSettings.topMarginMm} onChange={(e) => setRightSettings((p) => ({ ...p, topMarginMm: Number(e.target.value) || 0 }))} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={0} max={200} />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">하단 여백(mm)</span>
                                    <input type="number" value={rightSettings.bottomMarginMm} onChange={(e) => setRightSettings((p) => ({ ...p, bottomMarginMm: Number(e.target.value) || 0 }))} className="mt-1 w-full input-bevel px-3 py-2 text-sm" min={0} max={200} />
								</label>
                                <label className="block">
                                    <span className="block text-sm text-gray-600">가로 비율(%)</span>
                                    <input type="text" inputMode="numeric" pattern="[0-9]*" value={rightScaleXStr} onChange={(e) => {
                                        const v = e.target.value;
                                        if (/^\d{0,3}$/.test(v)) setRightScaleXStr(v);
                                    }} onBlur={() => {
                                        const n = Number(rightScaleXStr);
                                        const clamped = isNaN(n) ? Math.round(rightSettings.scaleX * 100) : Math.max(10, Math.min(300, n));
                                        setRightScaleXStr(String(clamped));
                                        setRightSettings((p) => ({ ...p, scaleX: clamped / 100 }));
                                    }} className="mt-1 w-full input-bevel px-3 py-2 text-sm" />
                                </label>
                                <label className="block">
                                    <span className="block text-sm text-gray-600">세로 비율(%)</span>
                                    <input type="text" inputMode="numeric" pattern="[0-9]*" value={rightScaleYStr} onChange={(e) => {
                                        const v = e.target.value;
                                        if (/^\d{0,3}$/.test(v)) setRightScaleYStr(v);
                                    }} onBlur={() => {
                                        const n = Number(rightScaleYStr);
                                        const clamped = isNaN(n) ? Math.round(rightSettings.scaleY * 100) : Math.max(10, Math.min(300, n));
                                        setRightScaleYStr(String(clamped));
                                        setRightSettings((p) => ({ ...p, scaleY: clamped / 100 }));
                                    }} className="mt-1 w-full input-bevel px-3 py-2 text-sm" />
                                </label>
							<label className="block">
								<span className="block text-sm text-gray-600">가로 정렬</span>
                                    <select value={rightSettings.horizontalAlign} onChange={(e) => setRightSettings((p) => ({ ...p, horizontalAlign: e.target.value as "left" | "center" | "right" }))} className="mt-1 w-full input-bevel px-3 py-2 text-sm">
									<option value="left">왼쪽</option>
									<option value="center">가운데</option>
									<option value="right">오른쪽</option>
								</select>
							</label>
							<label className="block">
								<span className="block text-sm text-gray-600">세로 방향</span>
                                    <select value={rightSettings.verticalDirection} onChange={(e) => setRightSettings((p) => ({ ...p, verticalDirection: e.target.value as "top-down" | "bottom-up" }))} className="mt-1 w-full input-bevel px-3 py-2 text-sm">
									<option value="top-down">위→아래</option>
									<option value="bottom-up">아래→위</option>
								</select>
							</label>
							<label className="inline-flex items-center gap-2 text-sm col-span-3"><input type="checkbox" checked={rightSettings.autoFit} onChange={(e) => setRightSettings((p) => ({ ...p, autoFit: e.target.checked }))} /> 리본 폭에 맞게 자동 폰트 크기</label>
							<label className="block col-span-3">
								<span className="block text-sm text-gray-600">양옆 여백(mm)</span>
								<input type="number" value={rightSettings.sidePaddingMm} onChange={(e) => setRightSettings((p) => ({ ...p, sidePaddingMm: Number(e.target.value) || 0 }))} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" min={0} max={20} />
							</label>
							</div>
						</div>

					{/* 전역 폰트 설정(스크립트별) — 위치 상단으로 이동 */}
                    <div className="rounded-md border p-3 mt-3">
						<div className="font-medium text-sm mb-2">폰트 설정(전역 · 스크립트별)</div>
                        <div className="flex items-center gap-2 mb-2 text-xs">
                            <button className="input-bevel px-2 py-1" onClick={loadSystemFonts} disabled={loadingSystemFonts}>{loadingSystemFonts? '불러오는 중...' : '시스템 폰트 불러오기(실험적)'}</button>
                            {systemFontError && <span className="text-red-600">{systemFontError}</span>}
                        </div>
                        <div className="grid grid-cols-3 gap-3 text-sm">
                            <label className="block">
                                <span className="block text-gray-600">한글</span>
                                <select value={fontKorean} onChange={(e) => setFontKorean(e.target.value)} className="mt-1 w-full input-bevel px-3 py-2">
                                    {envWebFonts.map(wf => (
                                        <option key={`wf_${wf.family}`} value={wf.family}>{wf.family}</option>
                                    ))}
                                    {systemFontList.filter(n => !envWebFonts.some(w => w.family === n)).map(name => (
                                        <option key={`sys_${name}`} value={name}>{name}</option>
                                    ))}
                                    {[...koreanFontOptions, ...windowsFontOptions]
                                        .filter(f => !systemFontList.includes(f.key) && !envWebFonts.some(w => w.family === f.key))
                                        .map(f => (<option key={f.key} value={f.key}>{f.label}</option>))}
                                    {![...koreanFontOptions, ...windowsFontOptions].some(f => f.key === fontKorean) && !systemFontList.includes(fontKorean) && !envWebFonts.some(w => w.family === fontKorean) && (
                                        <option value={fontKorean}>{fontKorean}</option>
                                    )}
                                </select>
                            </label>
                            <label className="block">
                                <span className="block text-gray-600">한자</span>
                                <select value={fontCjk} onChange={(e) => setFontCjk(e.target.value)} className="mt-1 w-full input-bevel px-3 py-2">
                                    {envWebFonts.map(wf => (
                                        <option key={`wf2_${wf.family}`} value={wf.family}>{wf.family}</option>
                                    ))}
                                    {systemFontList.filter(n => !envWebFonts.some(w => w.family === n)).map(name => (
                                        <option key={`sys2_${name}`} value={name}>{name}</option>
                                    ))}
                                    {[...windowsFontOptions, ...koreanFontOptions]
                                        .filter(f => !systemFontList.includes(f.key) && !envWebFonts.some(w => w.family === f.key))
                                        .map(f => (<option key={f.key} value={f.key}>{f.label}</option>))}
                                    {![...windowsFontOptions, ...koreanFontOptions].some(f => f.key === fontCjk) && !systemFontList.includes(fontCjk) && !envWebFonts.some(w => w.family === fontCjk) && (
                                        <option value={fontCjk}>{fontCjk}</option>
                                    )}
                                </select>
                            </label>
                            <label className="block">
                                <span className="block text-gray-600">영문</span>
                                <select value={fontLatin} onChange={(e) => setFontLatin(e.target.value)} className="mt-1 w-full input-bevel px-3 py-2">
                                    {envWebFonts.map(wf => (
                                        <option key={`wf3_${wf.family}`} value={wf.family}>{wf.family}</option>
                                    ))}
                                    {systemFontList.filter(n => !envWebFonts.some(w => w.family === n)).map(name => (
                                        <option key={`sys3_${name}`} value={name}>{name}</option>
                                    ))}
                                    {latinFontOptions
                                        .filter(f => !systemFontList.includes(f.key) && !envWebFonts.some(w => w.family === f.key))
                                        .map(f => (<option key={f.key} value={f.key}>{f.label}</option>))}
                                    {!latinFontOptions.some(f => f.key === fontLatin) && !systemFontList.includes(fontLatin) && !envWebFonts.some(w => w.family === fontLatin) && (
                                        <option value={fontLatin}>{fontLatin}</option>
                                    )}
                                </select>
                            </label>
							<p className="col-span-3 text-xs text-gray-500">여기서 지정한 폰트가 글자 유형(한글/한자/영문)에 따라 자동 적용됩니다.</p>
						</div>
					</div>

						{/* 표시/가이드 설정 */}
						<div className="rounded-md border p-3 mt-3">
							<div className="font-medium text-sm mb-2">표시/가이드</div>
							<div className="grid grid-cols-3 gap-3">
								<label className="inline-flex items-center gap-2 text-sm">
									<input type="checkbox" checked={showRuler} onChange={(e) => setShowRuler(e.target.checked)} /> 눈금 표시
								</label>
								<label className="inline-flex items-center gap-2 text-sm">
									<input type="checkbox" checked={showGuides} onChange={(e) => setShowGuides(e.target.checked)} /> 가이드 표시
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">상단 가이드(mm)</span>
									<input type="number" value={guide1Mm} onChange={(e) => setGuide1Mm(Number(e.target.value) || 0)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">하단 가이드(mm)</span>
									<input type="number" value={guide2Mm} onChange={(e) => setGuide2Mm(Number(e.target.value) || 0)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" />
								</label>
							</div>
						</div>

						{/* 출력 보정 */}
						<div className="rounded-md border p-3 mt-3">
							<div className="font-medium text-sm mb-2">출력 보정(베너 드라이버 대응)</div>
							<div className="grid grid-cols-3 gap-3">
								<label className="block">
									<span className="block text-sm text-gray-600">스케일(%)</span>
									<input type="number" value={printScalePercent} onChange={(e) => setPrintScalePercent(Number(e.target.value) || 100)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" min={10} max={300} />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">가로 오프셋(mm)</span>
									<input type="number" value={printOffsetXmm} onChange={(e) => setPrintOffsetXmm(Number(e.target.value) || 0)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" min={-100} max={100} />
								</label>
								<label className="block">
									<span className="block text-sm text-gray-600">세로 오프셋(mm)</span>
									<input type="number" value={printOffsetYmm} onChange={(e) => setPrintOffsetYmm(Number(e.target.value) || 0)} className="mt-1 w-full rounded-md border px-3 py-2 text-sm" min={-100} max={100} />
								</label>
								<label className="inline-flex items-center gap-2 text-sm col-span-3">
									<input type="checkbox" checked={applyCalibrationToDownload} onChange={(e) => setApplyCalibrationToDownload(e.target.checked)} /> 다운로드에 보정 적용
								</label>
							</div>
						</div>

                        {/* 배경색 — 위치를 폰트설정 아래로 이동 */}
                        <div className="grid grid-cols-3 gap-3 mt-3">
                            <label className="block">
                                <span className="block text-sm text-gray-600">배경색</span>
                                <input type="color" value={backgroundColor} onChange={(e) => setBackgroundColor(e.target.value)} className="mt-1 h-10 w-full rounded-md border px-2" />
                            </label>
                        </div>
					</div>
				</section>

                <section className="lg:col-span-2 rounded-lg border border-gray-200 p-4">
					<h2 className="font-medium mb-3">미리보기</h2>
                    <div ref={previewContainerRef} className="w-full overflow-auto border rounded-md p-6 bg-gray-50 flex items-start justify-center" style={{ maxHeight: Math.max(200, leftPanelHeight - 80) }}>
                        <div className={`flex gap-10`} style={{ transform: `scale(${effectiveScale})`, transformOrigin: 'top center' }}>
							<div>
								<canvas ref={leftCanvasRef} style={{ display: "block" }} />
								<div className="mt-2 flex gap-2 text-xs">
									<button onClick={() => handlePrint("left")} className="rounded border px-2 py-1"><Printer className="w-3 h-3" /> 좌 인쇄</button>
									<button onClick={() => handleDownload("left")} className="rounded border px-2 py-1"><Download className="w-3 h-3" /> 좌 저장</button>
								</div>
							</div>
							<div>
								<canvas ref={rightCanvasRef} style={{ display: "block" }} />
								<div className="mt-2 flex gap-2 text-xs">
									<button onClick={() => handlePrint("right")} className="rounded border px-2 py-1"><Printer className="w-3 h-3" /> 우 인쇄</button>
									<button onClick={() => handleDownload("right")} className="rounded border px-2 py-1"><Download className="w-3 h-3" /> 우 저장</button>
								</div>
							</div>
                        </div>
                        
                        {/* Ribbon Print Button */}
                        <div className="mt-4 flex justify-center">
                            <button 
                                onClick={() => {
                                    setPrintDialogOpen(true);
                                    if (installedPrinters.length === 0) {
                                        getInstalledPrinters();
                                    }
                                }} 
                                className="btn-blue px-4 py-2 rounded-lg flex items-center gap-2 text-white font-medium"
                            >
                                <Printer className="w-4 h-4" />
                                리본 프린트
                            </button>
                        </div>
					</div>
                </section>
        </div>
        <input ref={fileInputRef} type="file" accept="application/json" className="hidden" onChange={handleOpenJson} />
        {presetOpen && (
            <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <div className="panel rounded-lg w-full max-w-4xl p-4 bg-white">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-base font-semibold">리본 목록 편집</h3>
                        <button className="input-bevel px-2 py-1" onClick={() => setPresetOpen(false)}>닫기</button>
                    </div>
                    <div className="overflow-auto border rounded">
                        <table className="min-w-full text-xs">
                            <thead className="bg-gray-100">
                                <tr>
                                    <th className="px-2 py-2 text-left w-56">리본이름</th>
                                    <th className="px-2 py-2">넓이</th>
                                    <th className="px-2 py-2">레이스</th>
                                    <th className="px-2 py-2">길이</th>
                                    <th className="px-2 py-2">상단</th>
                                    <th className="px-2 py-2">하단</th>
                                    <th className="px-2 py-2">축소비율</th>
                                    <th className="px-2 py-2">가로비율</th>
                                    <th className="px-2 py-2">세로비율</th>
                                    <th className="px-2 py-2">여백</th>
                                    <th className="px-2 py-2">가로시작</th>
                                    <th className="px-2 py-2">세로시작</th>
                                    <th className="px-2 py-2"></th>
                                </tr>
                            </thead>
                            <tbody>
                                {presets.map((p, idx) => (
                                    <tr key={p.key || `${p.width}x${p.length}-${idx}`} className="odd:bg-white even:bg-gray-50">
                                        <td className="px-2 py-1 w-56"><input value={p.label} placeholder={`${p.width}x${p.length}mm`} onChange={(e)=>{
                                            const next=[...presets]; next[idx]={...p,label:e.target.value}; savePresets(next);
                                        }} className="input-bevel px-2 py-1 w-56 min-w-[220px]"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.width} onChange={(e)=>{const next=[...presets]; next[idx]={...p,width:Number(e.target.value)||0}; savePresets(next);}} className="w-20 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.laceMm} onChange={(e)=>{const next=[...presets]; next[idx]={...p,laceMm:Number(e.target.value)||0}; savePresets(next);}} className="w-20 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.length} onChange={(e)=>{const next=[...presets]; next[idx]={...p,length:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.topMm} onChange={(e)=>{const next=[...presets]; next[idx]={...p,topMm:Number(e.target.value)||0}; savePresets(next);}} className="w-20 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.bottomMm} onChange={(e)=>{const next=[...presets]; next[idx]={...p,bottomMm:Number(e.target.value)||0}; savePresets(next);}} className="w-20 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.bracketPercent} onChange={(e)=>{const next=[...presets]; next[idx]={...p,bracketPercent:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.scaleXPercent} onChange={(e)=>{const next=[...presets]; next[idx]={...p,scaleXPercent:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.scaleYPercent} onChange={(e)=>{const next=[...presets]; next[idx]={...p,scaleYPercent:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.marginMm} onChange={(e)=>{const next=[...presets]; next[idx]={...p,marginMm:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.startXmm} onChange={(e)=>{const next=[...presets]; next[idx]={...p,startXmm:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1"><input type="number" value={p.startYmm} onChange={(e)=>{const next=[...presets]; next[idx]={...p,startYmm:Number(e.target.value)||0}; savePresets(next);}} className="w-24 input-bevel px-2 py-1"/></td>
                                        <td className="px-2 py-1 text-right">
                                            <button className="px-2 py-1 text-red-600" onClick={()=>{
                                                const next=presets.filter((_,i)=>i!==idx);
                                                savePresets(next);
                                                if (p.key===selectedPreset && next[0]) applyPreset(next[0].key);
                                            }}>삭제</button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="flex items-center justify-between mt-3">
                        <button className="input-bevel px-3 py-2" onClick={()=>{
                            const id = `custom-${Date.now()}`;
                            const newItem: RibbonPreset = { key:id, label:"새 리본", width:38, length:400, laceMm:5, topMm:80, bottomMm:50, bracketPercent:70, scaleXPercent:100, scaleYPercent:100, marginMm:53, startXmm:0, startYmm:0 };
                            const next=[...presets, newItem];
                            savePresets(next);
                        }}>리본 추가</button>
                        <div className="flex items-center gap-2">
                            <button className="input-bevel px-3 py-2" onClick={()=>{ savePresets(defaultPresets); applyPreset(defaultPresets[0].key); }}>기본값 복원</button>
                            <button className="btn-blue px-3 py-2" onClick={()=> setPresetOpen(false)}>완료</button>
                        </div>
                    </div>
                </div>
            </div>
        )}
        {envOpen && (
            <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <div className="panel rounded-lg w-full max-w-2xl p-4 bg-white">
                    <div className="flex items-center justify-between mb-3">
                        <h3 className="text-base font-semibold">환경설정</h3>
                        <button className="input-bevel px-2 py-1" onClick={() => setEnvOpen(false)}>닫기</button>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <div className="font-medium mb-2">기본 프리셋</div>
                            <select value={envDefaultPreset} onChange={(e) => setEnvDefaultPreset(e.target.value)} className="input-bevel w-full px-3 py-2 text-sm">
                                {presets.map(p => <option key={p.key} value={p.key}>{p.label}</option>)}
                            </select>
                        </div>
                        <div>
                            <div className="font-medium mb-2">출력 보정 기본값</div>
                            <div className="grid grid-cols-3 gap-2 text-sm">
                                <label className="block">
                                    <span className="block text-gray-600">스케일(%)</span>
                                    <input type="number" value={envPrintScale} onChange={(e) => setEnvPrintScale(Number(e.target.value) || 100)} className="input-bevel w-full px-3 py-2" />
                                </label>
                                <label className="block">
                                    <span className="block text-gray-600">X(mm)</span>
                                    <input type="number" value={envOffsetXmm} onChange={(e) => setEnvOffsetXmm(Number(e.target.value) || 0)} className="input-bevel w-full px-3 py-2" />
                                </label>
                                <label className="block">
                                    <span className="block text-gray-600">Y(mm)</span>
                                    <input type="number" value={envOffsetYmm} onChange={(e) => setEnvOffsetYmm(Number(e.target.value) || 0)} className="input-bevel w-full px-3 py-2" />
                                </label>
                            </div>
                        </div>
                        <div className="col-span-2">
                            <div className="font-medium mb-2">기본 글꼴</div>
                            <div className="grid grid-cols-1 gap-3 text-sm">
                                <div className="grid grid-cols-4 gap-2 items-end">
                                    <label className="block col-span-2">
                                        <span className="block text-gray-600">소스</span>
                                        <select value={envFontSource} onChange={(e) => setEnvFontSource(e.target.value as "system" | "web")} className="input-bevel w-full px-3 py-2">
                                            <option value="system">시스템 폰트(Windows)</option>
                                            <option value="web">웹 폰트(URL)</option>
                                        </select>
                                    </label>
                                    <label className="block">
                                        <span className="block text-gray-600">글자 크기(px)</span>
                                        <input type="number" value={baseFontSizePx} onChange={(e) => setBaseFontSizePx(Number(e.target.value) || 12)} className="input-bevel w-full px-3 py-2" min={8} max={200} />
                                    </label>
                                </div>
                                {envFontSource === 'system' ? (
                                    <div className="grid grid-cols-3 gap-2">
                                        <label className="block col-span-2">
                                            <span className="block text-gray-600">시스템 글꼴</span>
                                            <select value={envSystemFont} onChange={(e) => { setEnvSystemFont(e.target.value); setBaseFontFamily(e.target.value); }} className="input-bevel w-full px-3 py-2">
                                                {[...windowsFontOptions, ...koreanFontOptions].map(f => <option key={f.key} value={f.key}>{f.label}</option>)}
                                            </select>
                                        </label>
                                        <div className="text-xs text-gray-500">PC에 설치된 글꼴명이면 브라우저가 사용합니다.</div>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        <div className="grid grid-cols-3 gap-2 items-end">
                                            <label className="block col-span-2">
                                                <span className="block text-gray-600">웹 폰트 CSS URL</span>
                                                <input value={envWebFontUrl} onChange={(e) => setEnvWebFontUrl(e.target.value)} placeholder="https://fonts.googleapis.com/css2?..." className="input-bevel w-full px-3 py-2" />
                                            </label>
                                            <label className="block">
                                                <span className="block text-gray-600">폰트 패밀리명</span>
                                                <input value={envWebFontFamily} onChange={(e) => setEnvWebFontFamily(e.target.value)} placeholder="예: LXGW WenKai TC" className="input-bevel w-full px-3 py-2" />
                                            </label>
                                        </div>
                                        <div>
                                            <button className="btn-blue px-3 py-2" onClick={() => {
                                                if (!envWebFontUrl || !envWebFontFamily) return;
                                                const item = { id: `wf-${Date.now()}`, url: envWebFontUrl, family: envWebFontFamily } as WebFontItem;
                                                const next = [...envWebFonts, item];
                                                setEnvWebFonts(next);
                                                injectAllWebFonts(next);
                                                setBaseFontFamily(envWebFontFamily);
                                                setEnvWebFontUrl(""); setEnvWebFontFamily("");
                                            }}>추가</button>
                                        </div>
                                        {envWebFonts.length > 0 && (
                                            <div className="rounded border p-2">
                                                <div className="text-xs text-gray-600 mb-1">등록된 웹 폰트</div>
                                                <ul className="space-y-1 text-sm">
                                                    {envWebFonts.map((f) => (
                                                        <li key={f.id} className="flex items-center justify-between gap-2">
                                                            <span className="truncate">{f.family}</span>
                                                            <div className="flex items-center gap-2">
                                                                <button className="input-bevel px-2 py-1" onClick={() => setBaseFontFamily(f.family)}>기본으로</button>
                                                                <button className="input-bevel px-2 py-1" onClick={() => {
                                                                    const next = envWebFonts.filter(x => x.id !== f.id);
                                                                    setEnvWebFonts(next);
                                                                    injectAllWebFonts(next);
                                                                }}>삭제</button>
                                                            </div>
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        )}
                                        <div className="grid grid-cols-1 gap-2">
                                            <label className="block">
                                                <span className="block text-gray-600">직접 CSS(@font-face) 붙여넣기</span>
                                                <textarea value={envWebFontCss} onChange={(e)=>setEnvWebFontCss(e.target.value)} className="input-bevel w-full px-3 py-2 text-xs" rows={5} placeholder="@font-face {\n  font-family: 'YourFamily';\n  src: url('https://.../your.woff2') format('woff2');\n  font-weight: 400; font-style: normal;\n}"></textarea>
                                            </label>
                                            <div className="flex items-center gap-2">
                                                <button className="input-bevel px-3 py-2" onClick={() => {
                                                    if (!envWebFontCss.trim()) return;
                                                    const fams = Array.from(new Set((envWebFontCss.match(/font-family\s*:\s*['\"]([^'\"]+)['\"]/gi) || []).map(s => s.replace(/.*font-family\s*:\s*['\"]/i,'').replace(/['\"];?/,'').trim())));
                                                    const item = { id: `wfc-${Date.now()}`, css: envWebFontCss, families: fams };
                                                    const next = [...envWebFontCssList, item];
                                                    setEnvWebFontCssList(next);
                                                    const id = `dynamic-webfont-css-${next.length-1}`;
                                                    let el = document.getElementById(id) as HTMLStyleElement | null;
                                                    if (!el) { el = document.createElement('style'); el.id = id; document.head.appendChild(el); }
                                                    el.textContent = envWebFontCss;
                                                    setFontLoadTick(t=>t+1);
                                                    setEnvWebFontCss('');
                                                }}>CSS 추가</button>
                                            </div>
                                            {envWebFontCssList.length>0 ? (
                                                <div className="rounded border p-2">
                                                    <div className="text-xs text-gray-600 mb-1">등록된 CSS 폰트</div>
                                                    <ul className="space-y-1 text-xs">
                                                        {envWebFontCssList.map((c, idx) => (
                                                            <li key={c.id} className="flex items-center justify-between gap-2">
                                                                <span className="truncate">{c.families.join(', ') || 'Custom CSS'}</span>
                                                                <button className="input-bevel px-2 py-1" onClick={()=>{
                                                                    const next = envWebFontCssList.filter(x=>x.id!==c.id);
                                                                    setEnvWebFontCssList(next);
                                                                    const node = document.getElementById(`dynamic-webfont-css-${idx}`);
                                                                    node?.parentElement?.removeChild(node);
                                                                    setFontLoadTick(t=>t+1);
                                                                }}>삭제</button>
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </div>
                                            ) : null}
                                        </div>
                                        <div className="text-xs text-gray-500">여러 URL/패밀리를 등록해 관리할 수 있습니다. 저장 시 함께 보관됩니다.</div>
                                        <div className="text-xs text-gray-500">전역 글꼴/크기 및 스크립트별 글꼴은 좌/우 리본 모두에 적용됩니다.</div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center justify-end gap-2 mt-4">
                        <button className="input-bevel px-3 py-2" onClick={() => setEnvOpen(false)}>취소</button>
                        <button className="btn-blue px-3 py-2" onClick={saveEnvironment}>저장</button>
                    </div>
                </div>
            </div>
        )}
        
        {/* Ribbon Print Dialog */}
        {printDialogOpen && (
            <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
                <div className="panel rounded-lg w-full max-w-md p-6 bg-white">
                    <div className="flex items-center justify-between mb-4">
                        <h3 className="text-lg font-semibold">리본 프린트 설정</h3>
                        <button onClick={() => setPrintDialogOpen(false)} className="text-gray-500 hover:text-gray-700">✕</button>
                    </div>
                    
                    <div className="space-y-4">
                        {/* Print Mode */}
                        <div>
                            <label className="block text-sm font-medium mb-2">출력 모드</label>
                            <div className="space-y-2">
                                <label className="flex items-center">
                                    <input 
                                        type="radio" 
                                        value="left" 
                                        checked={printMode === 'left'} 
                                        onChange={(e) => setPrintMode(e.target.value as 'left')}
                                        className="mr-2"
                                    />
                                    좌측만 (경조사)
                                </label>
                                <label className="flex items-center">
                                    <input 
                                        type="radio" 
                                        value="right" 
                                        checked={printMode === 'right'} 
                                        onChange={(e) => setPrintMode(e.target.value as 'right')}
                                        className="mr-2"
                                    />
                                    우측만 (보내는이)
                                </label>
                                <label className="flex items-center">
                                    <input 
                                        type="radio" 
                                        value="both" 
                                        checked={printMode === 'both'} 
                                        onChange={(e) => setPrintMode(e.target.value as 'both')}
                                        className="mr-2"
                                    />
                                    양쪽 동시 (좌측: 아래→위, 우측: 위→아래)
                                </label>
                            </div>
                        </div>
                        
                        {/* Installed Printers */}
                        <div>
                            <label className="block text-sm font-medium mb-2">설치된 프린터</label>
                            <div className="flex gap-2">
                                <select 
                                    value={selectedPrinter} 
                                    onChange={(e) => setSelectedPrinter(e.target.value)}
                                    className="input-bevel flex-1 px-3 py-2"
                                    disabled={loadingPrinters}
                                >
                                    {installedPrinters.length === 0 ? (
                                        <option value="">프린터 목록 로딩중...</option>
                                    ) : (
                                        installedPrinters.map((printer) => (
                                            <option key={printer} value={printer}>{printer}</option>
                                        ))
                                    )}
                                </select>
                                <button 
                                    onClick={getInstalledPrinters}
                                    disabled={loadingPrinters}
                                    className="input-bevel px-3 py-2 text-sm"
                                >
                                    {loadingPrinters ? '로딩...' : '새로고침'}
                                </button>
                            </div>
                        </div>
                        
                        {/* Ribbon Type */}
                        <div>
                            <label className="block text-sm font-medium mb-2">리본 타입</label>
                            <div className="space-y-2">
                                <label className="flex items-center">
                                    <input 
                                        type="radio" 
                                        checked={isRollRibbon} 
                                        onChange={() => setIsRollRibbon(true)}
                                        className="mr-2"
                                    />
                                    롤 리본 (연속 출력)
                                </label>
                                <label className="flex items-center">
                                    <input 
                                        type="radio" 
                                        checked={!isRollRibbon} 
                                        onChange={() => setIsRollRibbon(false)}
                                        className="mr-2"
                                    />
                                    재단 리본 (리본길이만큼 잘라서 급지)
                                </label>
                            </div>
                        </div>
                        
                        {/* Batch Mode (only for Roll Ribbon) */}
                        {isRollRibbon && (
                            <div>
                                <div className="flex items-center justify-between mb-2">
                                    <label className="text-sm font-medium">배치 출력 모드</label>
                                    <label className="flex items-center">
                                        <input 
                                            type="checkbox" 
                                            checked={batchMode} 
                                            onChange={(e) => setBatchMode(e.target.checked)}
                                            className="mr-2"
                                        />
                                        여러 리본 연속 출력
                                    </label>
                                </div>
                                
                                {batchMode && (
                                    <div className="space-y-3 p-3 bg-gray-50 rounded-lg">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm font-medium">리본 목록 ({ribbonBatch.filter(r => r.enabled).length}개 선택됨)</span>
                                            <button 
                                                onClick={addRibbonToBatch}
                                                className="text-xs bg-blue-500 text-white px-2 py-1 rounded"
                                            >
                                                현재 리본 추가
                                            </button>
                                        </div>
                                        
                                        <div className="max-h-32 overflow-y-auto space-y-2">
                                            {ribbonBatch.map((ribbon) => (
                                                <div key={ribbon.id} className="flex items-center gap-2 p-2 bg-white rounded border">
                                                    <input 
                                                        type="checkbox"
                                                        checked={ribbon.enabled}
                                                        onChange={() => toggleRibbonInBatch(ribbon.id)}
                                                        className="mr-1"
                                                    />
                                                    <div className="flex-1 grid grid-cols-2 gap-2 text-xs">
                                                        <input 
                                                            type="text"
                                                            value={ribbon.leftContent}
                                                            onChange={(e) => updateRibbonInBatch(ribbon.id, 'leftContent', e.target.value)}
                                                            placeholder="경조사"
                                                            className="border rounded px-1 py-0.5"
                                                        />
                                                        <input 
                                                            type="text"
                                                            value={ribbon.rightContent}
                                                            onChange={(e) => updateRibbonInBatch(ribbon.id, 'rightContent', e.target.value)}
                                                            placeholder="보내는이"
                                                            className="border rounded px-1 py-0.5"
                                                        />
                                                    </div>
                                                    <button 
                                                        onClick={() => removeRibbonFromBatch(ribbon.id)}
                                                        className="text-red-500 text-xs"
                                                    >
                                                        ✕
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                        
                                        <div>
                                            <label className="block text-xs font-medium mb-1">리본 간격 (mm)</label>
                                            <input 
                                                type="number"
                                                min="0"
                                                max="100"
                                                value={ribbonSpacingMm}
                                                onChange={(e) => setRibbonSpacingMm(parseInt(e.target.value) || 0)}
                                                className="input-bevel w-full px-2 py-1 text-sm"
                                            />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        
                        {/* Print Copies */}
                        <div>
                            <label className="block text-sm font-medium mb-2">매수</label>
                            <input 
                                type="number" 
                                min="1" 
                                max="999" 
                                value={printCopies} 
                                onChange={(e) => setPrintCopies(parseInt(e.target.value) || 1)}
                                className="input-bevel w-full px-3 py-2"
                            />
                        </div>
                        
                        {/* Advanced Settings */}
                        <div className="space-y-2">
                            <label className="flex items-center">
                                <input 
                                    type="checkbox" 
                                    checked={showCutLine} 
                                    onChange={(e) => setShowCutLine(e.target.checked)}
                                    className="mr-2"
                                />
                                중간구분선 인쇄 (좌우 구분선)
                            </label>
                        </div>
                        
                        {/* Print Settings */}
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">X-OFFSET</label>
                                <input 
                                    type="number" 
                                    value={xOffset} 
                                    onChange={(e) => setXOffset(parseInt(e.target.value) || 0)}
                                    className="input-bevel w-full px-2 py-1 text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium mb-1">
                                    배출(mm)
                                    {isRollRibbon && <span className="text-xs text-gray-500 block">출력 후 여분 리본 길이</span>}
                                </label>
                                <div className="flex items-center gap-2">
                                    <input 
                                        type="range"
                                        min="0"
                                        max="300"
                                        step="10"
                                        value={postFeed} 
                                        onChange={(e) => setPostFeed(parseInt(e.target.value))}
                                        className="flex-1"
                                        disabled={!isRollRibbon}
                                    />
                                    <input 
                                        type="number" 
                                        min="0"
                                        max="300"
                                        value={postFeed} 
                                        onChange={(e) => setPostFeed(parseInt(e.target.value) || 0)}
                                        className="input-bevel w-16 px-2 py-1 text-sm text-center"
                                        disabled={!isRollRibbon}
                                    />
                                    <span className="text-xs text-gray-500">mm</span>
                                </div>
                                {isRollRibbon && (
                                    <div className="text-xs text-gray-500 mt-1">
                                        권장: 50-150mm (잘라내기 편의용)
                                    </div>
                                )}
                            </div>
                        </div>
                        
                        {/* Print Speed */}
                        <div>
                            <label className="block text-sm font-medium mb-2">인쇄 속도</label>
                            <select 
                                value={printSpeed} 
                                onChange={(e) => setPrintSpeed(e.target.value as 'normal' | 'slow')}
                                className="input-bevel w-full px-3 py-2"
                            >
                                <option value="normal">보통</option>
                                <option value="slow">느리기</option>
                            </select>
                        </div>
                    </div>
                    
                    {/* Print Setup Instructions */}
                    <div className="bg-blue-50 p-4 rounded-lg mt-4">
                        <h4 className="font-medium text-blue-900 mb-2">📋 프린터 설정 안내</h4>
                        <div className="text-sm text-blue-800 space-y-1">
                            {isRollRibbon ? (
                                <>
                                    <div className="font-semibold text-blue-900">🎯 롤 리본 (연속 배너 출력)</div>
                                    <div><strong>1. 용지 크기:</strong> 사용자 정의 → {ribbonWidthMm}mm × <strong>연속</strong> (또는 매우 긴 길이)</div>
                                    <div><strong>2. 급지 방법:</strong> <strong>배너 모드</strong> 또는 <strong>연속 용지</strong></div>
                                    <div><strong>3. 용지 종류:</strong> <strong>배너</strong> 또는 <strong>롤 용지</strong></div>
                                    <div><strong>4. 방향:</strong> 세로(Portrait)</div>
                                    <div><strong>5. 여백:</strong> 0mm (여백 없음)</div>
                                    <div><strong>6. 배율:</strong> 100% (실제 크기)</div>
                                    <div><strong>7. 품질:</strong> 최고 품질</div>
                                    <div><strong>8. 배출:</strong> 출력 후 {postFeed}mm 여분 배출</div>
                                </>
                            ) : (
                                <>
                                    <div className="font-semibold text-blue-900">✂️ 재단 리본 (단일 출력)</div>
                                    <div><strong>1. 용지 크기:</strong> 사용자 정의 → {ribbonWidthMm}mm × {ribbonLengthMm}mm</div>
                                    <div><strong>2. 급지 방법:</strong> <strong>수동 급지</strong> (리본 길이만큼 잘라서 급지)</div>
                                    <div><strong>3. 용지 종류:</strong> <strong>일반 용지</strong></div>
                                    <div><strong>4. 방향:</strong> 세로(Portrait)</div>
                                    <div><strong>5. 여백:</strong> 0mm (여백 없음)</div>
                                    <div><strong>6. 배율:</strong> 100% (실제 크기)</div>
                                    <div><strong>7. 품질:</strong> 최고 품질</div>
                                </>
                            )}
                        </div>
                    </div>
                    
                    <div className="flex items-center justify-end gap-2 mt-6">
                        <button 
                            onClick={() => setPrintDialogOpen(false)} 
                            className="input-bevel px-4 py-2"
                        >
                            취소
                        </button>
                        <button 
                            onClick={executeRibbonPrint} 
                            className="btn-blue px-4 py-2 text-white"
                            disabled={!selectedPrinter}
                        >
                            {selectedPrinter ? '출력하기' : '프린터를 선택하세요'}
                        </button>
                    </div>
                </div>
            </div>
        )}
    </div>
  );
}


