// @ts-check
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  // Global ignores
  { ignores: ['dist', 'public', 'node_modules'] },
  
  // Base ESLint recommended config
  js.configs.recommended,
  
  // TypeScript ESLint recommended configs
  ...tseslint.configs.recommended,
  
  // React Hooks plugin
  reactHooks.configs['recommended-latest'],
  
  // React Refresh plugin (Vite)
  reactRefresh.configs.vite,
  
  // Main configuration for TypeScript and TSX files
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        ...globals.browser,
        ...globals.es2021,
      },
    },
    rules: {
      // React Refresh
      'react-refresh/only-export-components': 'off',
      
      // TypeScript
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_',
        },
      ],
      
      // React Hooks
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',
    },
  },
)
