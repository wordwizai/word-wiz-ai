import { useContext, useEffect, useState, useMemo } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  ArrowLeft,
  Copy,
  Check,
  Users,
  TrendingUp,
  BookOpen,
  Search,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { getClassStudents, type StudentWithStats } from "@/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

interface ClassDetailViewProps {
  classId: number;
  className: string;
  joinCode: string;
  onBack: () => void;
}

type SortField = "name" | "sessions" | "words" | "accuracy" | "last_active" | "streak";
type SortDirection = "asc" | "desc";

const ClassDetailView = ({
  classId,
  className,
  joinCode,
  onBack,
}: ClassDetailViewProps) => {
  const { token } = useContext(AuthContext);
  const [students, setStudents] = useState<StudentWithStats[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortField, setSortField] = useState<SortField>("name");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");

  useEffect(() => {
    fetchStudents();
  }, [classId, token]);

  const fetchStudents = async () => {
    if (!token) return;

    setLoading(true);
    setError("");
    try {
      const response = await getClassStudents(token, classId);
      setStudents(response.students);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load students");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyCode = () => {
    navigator.clipboard.writeText(joinCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  // Filter and sort students
  const filteredAndSortedStudents = useMemo(() => {
    let filtered = students.filter(
      (student) =>
        student.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        student.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    filtered.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case "name":
          comparison = (a.full_name || a.email).localeCompare(
            b.full_name || b.email
          );
          break;
        case "sessions":
          comparison = a.statistics.total_sessions - b.statistics.total_sessions;
          break;
        case "words":
          comparison = a.statistics.words_read - b.statistics.words_read;
          break;
        case "accuracy":
          comparison = a.statistics.average_per - b.statistics.average_per;
          break;
        case "last_active":
          const dateA = a.statistics.last_session_date
            ? new Date(a.statistics.last_session_date).getTime()
            : 0;
          const dateB = b.statistics.last_session_date
            ? new Date(b.statistics.last_session_date).getTime()
            : 0;
          comparison = dateA - dateB;
          break;
        case "streak":
          comparison = a.statistics.current_streak - b.statistics.current_streak;
          break;
      }
      return sortDirection === "asc" ? comparison : -comparison;
    });

    return filtered;
  }, [students, searchTerm, sortField, sortDirection]);

  // Calculate class statistics
  const classStats = useMemo(() => {
    if (students.length === 0) {
      return {
        totalStudents: 0,
        avgAccuracy: 0,
        totalSessions: 0,
        totalWords: 0,
      };
    }

    const totalSessions = students.reduce(
      (sum, s) => sum + s.statistics.total_sessions,
      0
    );
    const totalWords = students.reduce(
      (sum, s) => sum + s.statistics.words_read,
      0
    );
    const avgPer =
      students.reduce((sum, s) => sum + s.statistics.average_per, 0) /
      students.length;
    const avgAccuracy = (1 - avgPer) * 100;

    return {
      totalStudents: students.length,
      avgAccuracy: avgAccuracy.toFixed(1),
      totalSessions,
      totalWords,
    };
  }, [students]);

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null;
    return sortDirection === "asc" ? (
      <ChevronUp className="w-4 h-4 inline ml-1" />
    ) : (
      <ChevronDown className="w-4 h-4 inline ml-1" />
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={onBack}
                className="mb-2 -ml-2"
              >
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Classes
              </Button>
              <h1 className="text-2xl font-bold text-foreground">{className}</h1>
              <p className="text-sm text-muted-foreground mt-1">
                Class Management
              </p>
            </div>
          </div>

          {/* Join Code */}
          <div className="flex items-center gap-2 mb-4">
            <div className="flex-1 bg-muted p-3 rounded-lg">
              <p className="text-xs text-muted-foreground mb-1">Join Code</p>
              <p className="font-mono font-bold text-lg tracking-wider text-foreground">
                {joinCode}
              </p>
            </div>
            <Button
              variant="outline"
              size="icon"
              onClick={handleCopyCode}
              className="shrink-0"
            >
              {copied ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <Copy className="w-4 h-4" />
              )}
            </Button>
          </div>

          {/* Class Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-muted rounded-lg p-3">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <Users className="w-4 h-4" />
                <span className="text-xs">Students</span>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {classStats.totalStudents}
              </p>
            </div>
            <div className="bg-muted rounded-lg p-3">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <TrendingUp className="w-4 h-4" />
                <span className="text-xs">Avg Accuracy</span>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {classStats.avgAccuracy}%
              </p>
            </div>
            <div className="bg-muted rounded-lg p-3">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <BookOpen className="w-4 h-4" />
                <span className="text-xs">Total Sessions</span>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {classStats.totalSessions}
              </p>
            </div>
            <div className="bg-muted rounded-lg p-3">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <BookOpen className="w-4 h-4" />
                <span className="text-xs">Words Read</span>
              </div>
              <p className="text-2xl font-bold text-foreground">
                {classStats.totalWords}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Student Roster */}
      <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-foreground">Student Roster</h2>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                <Input
                  placeholder="Search students..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-9 w-64"
                />
              </div>
            </div>
          </div>

          {loading ? (
            <div className="text-center text-muted-foreground py-8">
              Loading students...
            </div>
          ) : error ? (
            <div className="text-center text-destructive py-8">{error}</div>
          ) : filteredAndSortedStudents.length === 0 ? (
            <div className="text-center text-muted-foreground py-8">
              {searchTerm ? "No students found matching your search." : "No students have joined this class yet."}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead
                      className="cursor-pointer hover:bg-muted"
                      onClick={() => handleSort("name")}
                    >
                      Student <SortIcon field="name" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted text-center"
                      onClick={() => handleSort("sessions")}
                    >
                      Sessions <SortIcon field="sessions" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted text-center"
                      onClick={() => handleSort("words")}
                    >
                      Words <SortIcon field="words" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted text-center"
                      onClick={() => handleSort("accuracy")}
                    >
                      Accuracy <SortIcon field="accuracy" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted text-center"
                      onClick={() => handleSort("streak")}
                    >
                      Streak <SortIcon field="streak" />
                    </TableHead>
                    <TableHead
                      className="cursor-pointer hover:bg-muted text-center"
                      onClick={() => handleSort("last_active")}
                    >
                      Last Active <SortIcon field="last_active" />
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredAndSortedStudents.map((student) => (
                    <TableRow key={student.id} className="hover:bg-muted/50">
                      <TableCell>
                        <div>
                          <p className="font-medium text-foreground">
                            {student.full_name || "Student"}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {student.email}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="text-center">
                        {student.statistics.total_sessions}
                      </TableCell>
                      <TableCell className="text-center">
                        {student.statistics.words_read}
                      </TableCell>
                      <TableCell className="text-center">
                        <span
                          className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                            student.statistics.average_per < 0.1
                              ? "bg-green-100 text-green-800"
                              : student.statistics.average_per < 0.2
                              ? "bg-yellow-100 text-yellow-800"
                              : "bg-orange-100 text-orange-800"
                          }`}
                        >
                          {student.statistics.average_per > 0
                            ? `${((1 - student.statistics.average_per) * 100).toFixed(1)}%`
                            : "N/A"}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        {student.statistics.current_streak} days
                      </TableCell>
                      <TableCell className="text-center text-sm text-muted-foreground">
                        {formatDate(student.statistics.last_session_date)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};

export default ClassDetailView;
