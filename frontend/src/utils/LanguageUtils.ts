// frontend/src/utils/languageUtils.ts
export const getLanguageDisplay = (langCode: string): string => {
  const languages: { [key: string]: string } = {
    'hu': 'Magyar',
    'en': 'English',
    'de': 'Deutsch',
    'sk': 'Slovenčina',
    'ro': 'Română',
    'hr': 'Hrvatski',
    'sr': 'Српски',
  };
  
  return languages[langCode] || langCode.toUpperCase();
};

export const getSeverityText = (severity: string, language: string = 'hu'): string => {
  if (language === 'hu') {
    const severityTexts: { [key: string]: string } = {
      'critical': 'Kritikus',
      'high': 'Magas',
      'medium': 'Közepes',
      'low': 'Alacsony',
    };
    return severityTexts[severity] || severity;
  }
  
  // Default to English
  return severity.charAt(0).toUpperCase() + severity.slice(1);
};

export const getCategoryText = (category: string, language: string = 'hu'): string => {
  if (language === 'hu') {
    const categoryTexts: { [key: string]: string } = {
      'technical': 'Technikai',
      'content': 'Tartalom',
      'performance': 'Teljesítmény',
      'accessibility': 'Akadálymentesség',
      'social': 'Közösségi média',
    };
    return categoryTexts[category] || category;
  }
  
  return category.charAt(0).toUpperCase() + category.slice(1);
};
