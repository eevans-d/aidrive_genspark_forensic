module.exports = {
  // Test environment
  testEnvironment: 'node',
  
  // Directories
  roots: ['<rootDir>/tests'],
  testMatch: [
    '**/tests/**/*.test.{js,ts}',
    '**/tests/**/*.spec.{js,ts}'
  ],
  
  // Coverage settings
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  collectCoverageFrom: [
    '/workspace/supabase/functions/**/*.ts',
    '!**/node_modules/**',
    '!**/coverage/**',
    '!**/tests/**',
    '!**/*.d.ts'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 85,
      statements: 85
    }
  },
  
  // Test file patterns
  testPathIgnorePatterns: [
    '/node_modules/',
    '/coverage/',
    '/dist/'
  ],
  
  // Module file extensions
  moduleFileExtensions: ['ts', 'js', 'json'],
  
  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/helpers/setup.js'],
  
  // Transform settings for TypeScript
  transform: {
    '^.+\\.ts$': 'ts-jest'
  },
  
  // Global test settings
  globals: {
    'ts-jest': {
      tsconfig: {
        target: 'ES2020',
        module: 'commonjs',
        lib: ['ES2020'],
        esModuleInterop: true,
        allowSyntheticDefaultImports: true,
        experimentalDecorators: true,
        emitDecoratorMetadata: true,
        skipLibCheck: true
      }
    }
  },
  
  // Test timeout
  testTimeout: 30000,
  
  // Verbose output
  verbose: true
};