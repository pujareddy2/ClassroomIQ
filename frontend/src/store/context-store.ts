import { create } from 'zustand'
import { persist } from 'zustand/middleware'

type ContextState = { 
  selectedLectureId: string | null; 
  selectedCourseId: string | null; 
  selectedCourseName: string | null; 
  selectedCurriculumId: string | null; 
  semester: string | null; 
  setLectureId: (id: string | null) => void; 
  setCourseId: (id: string | null, name?: string | null) => void; 
  setCurriculumId: (id: string | null) => void; 
  setSemester: (semester: string | null) => void 
}

export const useContextStore = create<ContextState>()(persist((set) => ({ 
  selectedLectureId: null, 
  selectedCourseId: null, 
  selectedCourseName: null, 
  selectedCurriculumId: null, 
  semester: null, 
  setLectureId: (selectedLectureId) => set({ selectedLectureId }), 
  setCourseId: (selectedCourseId, selectedCourseName) => set({ selectedCourseId, ...(selectedCourseName !== undefined ? { selectedCourseName } : {}) }), 
  setCurriculumId: (selectedCurriculumId) => set({ selectedCurriculumId }), 
  setSemester: (semester) => set({ semester }) 
}), { name: 'classroomiq-context' }))
