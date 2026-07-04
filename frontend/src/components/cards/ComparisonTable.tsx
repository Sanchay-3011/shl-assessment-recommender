import React from 'react';
import { Clock, Globe, Shield, Laptop, Layers } from 'lucide-react';

interface ComparisonTableProps {
  targets: string[];
}

const COMPARISON_POPULAR_DETAILS: Record<string, {
  category: string;
  duration: string;
  adaptive: string;
  remote: string;
  languages: string;
  levels: string;
  description: string;
}> = {
  "OPQ MQ Sales Report": {
    category: "Personality & Behavior",
    duration: "25 minutes",
    adaptive: "Yes (Adaptive)",
    remote: "Yes (Remote proctored)",
    languages: "English, Spanish, French",
    levels: "Manager, Director, Mid-Professional",
    description: "Evaluates behavior, drives, and sales motivators."
  },
  "Sales Interview Guide": {
    category: "Interview Support",
    duration: "Reference card",
    adaptive: "No (Fixed layout)",
    remote: "Yes (Document link)",
    languages: "English (USA)",
    levels: "Mid-Professional, Recruiter",
    description: "Maps OPQ traits to standard structural competency questions."
  },
  "Customer Service Phone Simulation": {
    category: "Simulations",
    duration: "15 minutes",
    adaptive: "No (Fixed form)",
    remote: "Yes (Remote proctored)",
    languages: "English (USA), Spanish",
    levels: "Entry-Level, Graduate",
    description: "Interactive voice simulation resolving customer inquiries."
  },
  "Customer Service Phone Solution": {
    category: "Simulations & Behavioral",
    duration: "20 minutes",
    adaptive: "Yes (Multi-part)",
    remote: "Yes (Remote proctored)",
    languages: "English (USA)",
    levels: "Entry-Level",
    description: "Includes the phone simulation plus behavioral profiles."
  },
  "Sales Transformation Report 1.0 - Sales Manager": {
    category: "Personality & Leadership",
    duration: "25 minutes",
    adaptive: "Yes (Adaptive)",
    remote: "Yes (Remote proctored)",
    languages: "English (USA)",
    levels: "Manager, Lead",
    description: "Behavioral fit for managers leading sales transformations."
  },
  "Sales Transformation Report 2.0 - Sales Manager": {
    category: "Personality & Leadership (V2)",
    duration: "25 minutes",
    adaptive: "Yes (Adaptive)",
    remote: "Yes (Remote proctored)",
    languages: "English (USA)",
    levels: "Manager, Lead",
    description: "Refined digital-first behavioral framework updates."
  },
  "Core Java (Entry Level) (New)": {
    category: "Knowledge & Skills",
    duration: "25 minutes",
    adaptive: "Yes (Adaptive)",
    remote: "Yes (Remote)",
    languages: "English (USA)",
    levels: "Entry-Level, Graduate",
    description: "Screens basic Java programming constructs, files, and exceptions."
  },
  "Core Java (Advanced Level) (New)": {
    category: "Knowledge & Skills",
    duration: "30 minutes",
    adaptive: "Yes (Adaptive)",
    remote: "Yes (Remote)",
    languages: "English (USA)",
    levels: "Mid-Professional, Lead",
    description: "Assesses advanced concurrency, collections, and generic models."
  }
};

export const ComparisonTable: React.FC<ComparisonTableProps> = ({ targets }) => {
  // Map target items to details
  const details = targets.map((t) => {
    return {
      name: t,
      data: COMPARISON_POPULAR_DETAILS[t] || {
        category: "Hiring Solution",
        duration: "20-30 minutes",
        adaptive: "Yes (Adaptive)",
        remote: "Yes (Remote proctored)",
        languages: "English (USA)",
        levels: "Mid-Professional",
        description: "SHL Catalog assessment."
      }
    };
  });

  return (
    <div className="border border-slate-200 rounded-2xl overflow-hidden bg-white shadow-sm my-4 select-none">
      <table className="w-full text-left border-collapse text-xs">
        <thead>
          <tr className="bg-slate-50 border-b border-slate-200 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <th className="p-4 w-40 font-bold">Feature</th>
            {details.map((d, idx) => (
              <th key={idx} className="p-4 font-bold text-slate-800 border-l border-slate-100">
                {d.name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 font-medium text-slate-600">
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Category</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100">{d.data.category}</td>
            ))}
          </tr>
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Duration</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-400" />
                <span>{d.data.duration}</span>
              </td>
            ))}
          </tr>
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Adaptivity</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100 flex items-center space-x-1.5">
                <Shield className="w-3.5 h-3.5 text-slate-400" />
                <span>{d.data.adaptive}</span>
              </td>
            ))}
          </tr>
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Proctoring</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100 flex items-center space-x-1.5">
                <Laptop className="w-3.5 h-3.5 text-slate-400" />
                <span>{d.data.remote}</span>
              </td>
            ))}
          </tr>
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Languages</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100 flex items-center space-x-1.5">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <span>{d.data.languages}</span>
              </td>
            ))}
          </tr>
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Job Levels</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100 flex items-center space-x-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                <span className="truncate max-w-[200px]">{d.data.levels}</span>
              </td>
            ))}
          </tr>
          <tr>
            <td className="p-4 font-semibold text-slate-500 bg-slate-50/50">Objective</td>
            {details.map((d, idx) => (
              <td key={idx} className="p-4 border-l border-slate-100 text-slate-500 font-normal italic">
                {d.data.description}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
};
