import { useContextStore } from '@/store/context-store'

export const useCurrentCourse = () => useContextStore((state) => ({ courseId: state.selectedCourseId, setCourseId: state.setCourseId, semester: state.semester, setSemester: state.setSemester }))
export const useCurrentCurriculum = () => useContextStore((state) => ({ curriculumId: state.selectedCurriculumId, setCurriculumId: state.setCurriculumId }))
export const useCurrentLecture = () => useContextStore((state) => ({ lectureId: state.selectedLectureId, setLectureId: state.setLectureId }))
