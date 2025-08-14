import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    rules: {
      "react-hooks/exhaustive-deps": "off", // useEffect 의존성 배열 경고 비활성화
      "@typescript-eslint/no-unused-vars": "warn", // 사용되지 않는 변수는 경고로만
    }
  }
];

export default eslintConfig;
