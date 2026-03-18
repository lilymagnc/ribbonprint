export interface CustomFontInfo {
  id: string; // matches CSS class name
  name: string;
  source: 'web' | 'local';
  webUrl?: string; // either standard font family name or gfont URL
  fontFamily?: string; 
  blob?: Blob; // For local fonts
}

// IndexedDB setup
const DB_NAME = 'RibbonFontsDB';
const STORE_NAME = 'localFonts';

export const initDB = () => {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, 1);
    request.onupgradeneeded = (e) => {
      const db = (e.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id' });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
};

export const saveCustomFontToDB = async (font: CustomFontInfo) => {
  const db = await initDB();
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    store.put(font);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
};

export const getAllCustomFonts = async (): Promise<CustomFontInfo[]> => {
  const db = await initDB();
  return new Promise<CustomFontInfo[]>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const store = tx.objectStore(STORE_NAME);
    const request = store.getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
};

export const deleteCustomFontFromDB = async (id: string) => {
  const db = await initDB();
  return new Promise<void>((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    const store = tx.objectStore(STORE_NAME);
    store.delete(id);
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error);
  });
};

export const getHiddenFonts = (): string[] => {
  try {
    const hidden = localStorage.getItem('hiddenFonts');
    if (hidden) return JSON.parse(hidden);
  } catch (e) {
    console.error(e);
  }
  return [];
};

export const setHiddenFonts = (ids: string[]) => {
  localStorage.setItem('hiddenFonts', JSON.stringify(ids));
};
