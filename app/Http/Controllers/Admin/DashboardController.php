<?php

namespace App\Http\Controllers\Admin;

use App\Http\Controllers\Controller;
use App\Models\AppointmentBooking;
use App\Models\Doctor;
use Illuminate\Http\Request;
use App\Models\User;

class DashboardController extends Controller
{
    public function index(){
        // User Statistics
        $totalUsers = User::count();
        $totalPatients = User::where('role', 'patient')->count();
        $totalDoctors = User::where('role', 'doctor')->count();
        $totalAdmins = User::where('role', 'admin')->count();


        // Doctor Statistics
        $approvedDoctors = User::where('role', 'doctor')->where('status', 'approved')->count();
        $pendingDoctors = User::where('role', 'doctor')->where('status', 'pending')->get();
        $rejectedDoctors = User::where('role', 'doctor')->where('status', 'rejected')->count();

        // Appointment Statistics
        $totalAppointments = AppointmentBooking::count();
        $pendingAppointments = AppointmentBooking::where('status', 'pending')->count();
        $approvedAppointments = AppointmentBooking::where('status', 'approved')->count();
        $completedAppointments = AppointmentBooking::where('status', 'completed')->count();
        $cancelledAppointments = AppointmentBooking::where('status', 'cancelled')->count();

        // Chart Data - Users by Role
        $usersByRole = [
            'Patients' => $totalPatients,
            'Doctors' => $totalDoctors,
            'Admins' => $totalAdmins,
        ];

        // Chart Data - Appointments by Status
        $appointmentsByStatus = [
            'Pending' => $pendingAppointments,
            'Approved' => $approvedAppointments,
            'Completed' => $completedAppointments,
            'Cancelled' => $cancelledAppointments,
        ];

        // Chart Data - Doctors by Specialization
        $doctorsBySpecialization = Doctor::select('specialist')
            ->selectRaw('count(*) as count')
            ->groupBy('specialist')
            ->get()
            ->pluck('count', 'specialist')
            ->toArray();

        $chartData = [
            'usersByRole' => $usersByRole,
            'appointmentsByStatus' => $appointmentsByStatus,
            'doctorsBySpecialization' => $doctorsBySpecialization,
        ];

        return view('admin.dashboard', compact([
            'pendingDoctors', 'totalDoctors', 'totalPatients',
            'totalUsers', 'totalAdmins', 'approvedDoctors', 'rejectedDoctors',
            'totalAppointments', 'pendingAppointments', 'approvedAppointments',
            'completedAppointments', 'cancelledAppointments', 'chartData'
        ]));
    }

    public function getStatisticsByDate(Request $request): \Illuminate\Http\JsonResponse
    {
        $date = $request->input('date');

        if (!$date) {
            $date = now()->toDateString();
        }

        // Convert to date range (entire day)
        $startOfDay = \Carbon\Carbon::createFromFormat('Y-m-d', $date)->startOfDay();
        $endOfDay = \Carbon\Carbon::createFromFormat('Y-m-d', $date)->endOfDay();

        // Appointment Statistics for the date
        $totalAppointments = AppointmentBooking::whereBetween('created_at', [$startOfDay, $endOfDay])->count();
        $pendingAppointments = AppointmentBooking::whereBetween('created_at', [$startOfDay, $endOfDay])->where('status', 'pending')->count();
        $approvedAppointments = AppointmentBooking::whereBetween('created_at', [$startOfDay, $endOfDay])->where('status', 'approved')->count();
        $completedAppointments = AppointmentBooking::whereBetween('created_at', [$startOfDay, $endOfDay])->where('status', 'completed')->count();
        $cancelledAppointments = AppointmentBooking::whereBetween('created_at', [$startOfDay, $endOfDay])->where('status', 'cancelled')->count();

        // User Statistics (overall, not date-filtered as user creation doesn't need date filter for dashboard)
        $totalUsers = User::count();
        $totalPatients = User::where('role', 'patient')->count();
        $totalDoctors = User::where('role', 'doctor')->count();
        $totalAdmins = User::where('role', 'admin')->count();
        $approvedDoctors = User::where('role', 'doctor')->where('status', 'approved')->count();
        $rejectedDoctors = User::where('role', 'doctor')->where('status', 'rejected')->count();

        // Chart Data - Users by Role
        $usersByRole = [
            'Patients' => $totalPatients,
            'Doctors' => $totalDoctors,
            'Admins' => $totalAdmins,
        ];

        // Chart Data - Appointments by Status
        $appointmentsByStatus = [
            'Pending' => $pendingAppointments,
            'Approved' => $approvedAppointments,
            'Completed' => $completedAppointments,
            'Cancelled' => $cancelledAppointments,
        ];

        // Chart Data - Doctors by Specialization
        $doctorsBySpecialization = Doctor::select('specialist')
            ->selectRaw('count(*) as count')
            ->groupBy('specialist')
            ->get()
            ->pluck('count', 'specialist')
            ->toArray();

        return response()->json([
            'date' => $date,
            'totalUsers' => $totalUsers,
            'totalPatients' => $totalPatients,
            'totalDoctors' => $totalDoctors,
            'totalAdmins' => $totalAdmins,
            'approvedDoctors' => $approvedDoctors,
            'rejectedDoctors' => $rejectedDoctors,
            'totalAppointments' => $totalAppointments,
            'pendingAppointments' => $pendingAppointments,
            'approvedAppointments' => $approvedAppointments,
            'completedAppointments' => $completedAppointments,
            'cancelledAppointments' => $cancelledAppointments,
            'chartData' => [
                'usersByRole' => $usersByRole,
                'appointmentsByStatus' => $appointmentsByStatus,
                'doctorsBySpecialization' => $doctorsBySpecialization,
            ]
        ]);
    }

    public function approveDoctor($id){
        $user = User::findOrFail($id);
        $user->role = 'doctor';
        $user->status = 'approved';
        $user->save();
        return redirect()->back()->with('success', 'Doctor approved successfully');
    }

    public function rejectDoctor($id){
        $user = User::findOrFail($id);
        $user->status = 'rejected';
        $user->save();
        return redirect()->back();
    }

    public function notification(){
        $notifications = auth()->user()->notifications()->latest()->get();
        // Mark as read
        auth()->user()->unreadNotifications()->update(['read_at' => now()]);
        return view('admin.Notifications', compact('notifications'));
    }

    public function getNotificationCount(){
        $count = auth()->user()->unreadNotifications()->count();
        return response()->json(['count' => $count]);
    }

    public function user(Request $request){
        $search = $request->input('search');
        $users = User::when($search, function($query, $search){
            return $query->where('name', 'like', "%{$search}%");
        })->paginate(10);
        return view('admin.User', compact('users'));
    }
}
