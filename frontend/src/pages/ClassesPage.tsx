import { useContext, useEffect, useState } from "react";
import { AuthContext } from "@/contexts/AuthContext";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Plus, Users } from "lucide-react";
import {
  getMyClasses,
  getMyStudentClasses,
  type Class,
  type ClassWithTeacher,
} from "@/api";
import CreateClassDialog from "@/components/classes/CreateClassDialog";
import JoinClassDialog from "@/components/classes/JoinClassDialog";
import ClassCard from "@/components/classes/ClassCard";

const ClassesPage = () => {
  const { token } = useContext(AuthContext);
  const [myClasses, setMyClasses] = useState<Class[]>([]);
  const [studentClasses, setStudentClasses] = useState<ClassWithTeacher[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showJoinDialog, setShowJoinDialog] = useState(false);

  useEffect(() => {
    fetchClasses();
  }, [token]);

  const fetchClasses = async () => {
    if (!token) return;

    setLoading(true);
    try {
      const [teacherClasses, enrolledClasses] = await Promise.all([
        getMyClasses(token),
        getMyStudentClasses(token),
      ]);
      setMyClasses(teacherClasses);
      setStudentClasses(enrolledClasses);
    } catch (error) {
      console.error("Error fetching classes:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleClassCreated = () => {
    setShowCreateDialog(false);
    fetchClasses();
  };

  const handleClassJoined = () => {
    setShowJoinDialog(false);
    fetchClasses();
  };

  const handleClassDeleted = () => {
    fetchClasses();
  };

  const handleClassLeft = () => {
    fetchClasses();
  };

  return (
    <main className="flex-1 p-4 sm:p-6 bg-background space-y-6 overflow-y-auto flex flex-col min-h-0 h-full">
      {/* Header */}
      <div className="relative rounded-2xl overflow-hidden bg-gradient-to-br from-primary/10 via-accent/5 to-primary/5 border border-primary/20 p-6">
        <div className="relative z-10 flex items-center justify-between">
          <div>
            <h1 className="text-2xl md:text-4xl font-bold text-foreground mb-2">
              Classes
            </h1>
            <p className="text-sm md:text-base text-muted-foreground/80">
              Manage your classes and view student progress
            </p>
          </div>
          <Users className="w-12 h-12 md:w-16 md:h-16 text-primary/20" />
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="my-classes" className="flex-1 flex flex-col min-h-0">
        <TabsList className="grid w-full grid-cols-2 mb-4">
          <TabsTrigger value="my-classes">My Classes</TabsTrigger>
          <TabsTrigger value="join">Join Class</TabsTrigger>
        </TabsList>

        {/* My Classes Tab */}
        <TabsContent
          value="my-classes"
          className="flex-1 overflow-y-auto space-y-4"
        >
          {/* Teacher's Classes */}
          <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
            <CardHeader className="p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-foreground">
                  Classes I Teach
                </h2>
                <Button
                  onClick={() => setShowCreateDialog(true)}
                  className="bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90"
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Create Class
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              {loading ? (
                <div className="text-center text-muted-foreground py-8">
                  Loading...
                </div>
              ) : myClasses.length > 0 ? (
                <div className="space-y-3">
                  {myClasses.map((classItem) => (
                    <ClassCard
                      key={classItem.id}
                      classItem={classItem}
                      isTeacher={true}
                      onDeleted={handleClassDeleted}
                      onLeft={handleClassLeft}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <p>You haven't created any classes yet.</p>
                  <p className="text-sm mt-2">
                    Click "Create Class" to get started!
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Student's Enrolled Classes */}
          <Card className="rounded-2xl bg-card border-2 border-border shadow-md">
            <CardHeader className="p-4">
              <h2 className="text-lg font-bold text-foreground">
                Classes I'm Enrolled In
              </h2>
            </CardHeader>
            <CardContent className="p-4 pt-0">
              {loading ? (
                <div className="text-center text-muted-foreground py-8">
                  Loading...
                </div>
              ) : studentClasses.length > 0 ? (
                <div className="space-y-3">
                  {studentClasses.map((classItem) => (
                    <ClassCard
                      key={classItem.id}
                      classItem={classItem}
                      isTeacher={false}
                      onDeleted={handleClassDeleted}
                      onLeft={handleClassLeft}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center text-muted-foreground py-8">
                  <p>You haven't joined any classes yet.</p>
                  <p className="text-sm mt-2">
                    Use the "Join Class" tab to join a class!
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Join Class Tab */}
        <TabsContent value="join" className="flex-1">
          <JoinClassDialog
            onJoined={handleClassJoined}
            showAsCard={true}
          />
        </TabsContent>
      </Tabs>

      {/* Dialogs */}
      <CreateClassDialog
        open={showCreateDialog}
        onOpenChange={setShowCreateDialog}
        onCreated={handleClassCreated}
      />
    </main>
  );
};

export default ClassesPage;
