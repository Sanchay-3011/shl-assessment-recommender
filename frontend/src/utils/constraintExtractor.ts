import type { ChatMessage, HiringConstraints } from '../types';

const COMMON_TECH_VOCAB = new Set<string>([
  'python', 'java', 'javascript', 'c#', 'salesforce', 'sap', '.net', 'html', 'css',
  'typing', 'numerical', 'verbal', 'cognitive', 'excel', 'sql', 'c++', 'react', 'node'
]);

export const extractConstraintsFromHistory = (messages: ChatMessage[]): HiringConstraints => {
  const constraints: HiringConstraints = {
    role: null,
    skills: [],
    programming_languages: [],
    job_level: null,
    experience: null,
    duration: null,
    language: null,
    adaptive: null,
    remote: null,
    assessment_keys: []
  };

  messages.forEach((msg) => {
    if (msg.role !== 'user') return;

    const text = msg.content.toLowerCase();

    // 1. Role and Skills
    const words = text.match(/\b[a-zA-Z0-9+#.-]+\b/g) || [];
    const matchedVocab: string[] = [];
    words.forEach((w) => {
      if (COMMON_TECH_VOCAB.has(w)) {
        const cap = w === 'c#' ? 'C#' : w === '.net' ? '.NET' : w.charAt(0).toUpperCase() + w.slice(1);
        if (!matchedVocab.includes(cap)) {
          matchedVocab.push(cap);
        }
      }
    });

    if (matchedVocab.length > 0) {
      constraints.role = matchedVocab[0];
      if (matchedVocab.length > 1) {
        constraints.skills = matchedVocab.slice(1);
      }
    }

    // 2. Job Level
    const levelPatterns = {
      'Entry-Level': ['entry-level', 'junior', 'entry level'],
      'Graduate': ['graduate', 'intern'],
      'Mid-Professional': ['mid-professional', 'mid-level', 'middle', 'intermediate'],
      'Manager': ['manager', 'lead'],
      'Director': ['director', 'head of']
    };

    for (const [level, keywords] of Object.entries(levelPatterns)) {
      if (keywords.some((kw) => text.includes(kw))) {
        constraints.job_level = level;
      }
    }

    // 3. Duration
    const durationMatch = text.match(/(\d+)\s*(?:minutes|minute|min)/);
    if (durationMatch) {
      constraints.duration = parseInt(durationMatch[1], 10);
    }

    // 4. Preferred Language
    const languages = ['english', 'spanish', 'french', 'german', 'italian', 'chinese', 'japanese'];
    languages.forEach((lang) => {
      if (text.includes(lang)) {
        constraints.language = lang.charAt(0).toUpperCase() + lang.slice(1);
      }
    });

    // 5. Adaptive
    if (text.includes('adaptive')) {
      if (text.includes('no ') || text.includes('exclude') || text.includes('not ')) {
        constraints.adaptive = 'no';
      } else {
        constraints.adaptive = 'yes';
      }
    }

    // 6. Remote
    if (text.includes('remote')) {
      if (text.includes('no ') || text.includes('exclude') || text.includes('not ')) {
        constraints.remote = 'no';
      } else {
        constraints.remote = 'yes';
      }
    }

    // 7. Assessment Keys (Categories)
    const categoryPatterns = {
      'Ability & Aptitude': ['aptitude', 'cognitive', 'ability', 'reasoning', 'analytical', 'gsa'],
      'Personality & Behavior': ['personality', 'behavior', 'opq', 'stakeholder', 'work with', 'interpersonal', 'soft skills'],
      'Simulations': ['simulation', 'interactive'],
      'Knowledge & Skills': ['knowledge', 'skills', 'coding', 'technical', 'programming']
    };

    for (const [category, keywords] of Object.entries(categoryPatterns)) {
      if (keywords.some((kw) => text.includes(kw))) {
        if (!constraints.assessment_keys.includes(category)) {
          constraints.assessment_keys.push(category);
        }
      }
    }

    // Handle exclusions
    if (text.includes('exclude coding') || text.includes('no coding')) {
      constraints.assessment_keys = constraints.assessment_keys.filter((k) => k !== 'Knowledge & Skills');
    }
  });

  return constraints;
};
