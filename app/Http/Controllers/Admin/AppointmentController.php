<?php

namespace App\Http\Controllers\Admin;

use App\Models\AppointmentBooking;
use App\Models\AppointmentSchedule;
use App\Models\User;
use Illuminate\Http\Request;
//ok this works
class AppointmentController
{
    public function index(Request $request)
    {
        $search = $request->input('search');
        $status = $request->input('status');

        $appointments = AppointmentBooking::with(['schedule.doctor', 'patient'])
            ->when($search, function ($query, $search) {
                return $query->whereHas('patient', function ($q) use ($search) {
                    $q->where('name', 'like', "%{$search}%");
                })->orWhereHas('schedule.doctor', function ($q) use ($search) {
                    $q->where('name', 'like', "%{$search}%");
                });
            })
            ->when($status, function ($query, $status) {
                return $query->where('status', $status);
            })
            ->orderBy('created_at', 'desc')
            ->paginate(15);

        return view('admin.appointments.index', compact('appointments', 'search', 'status'));
    }

    public function show(AppointmentBooking $appointment)
    {
        $appointment->load(['schedule.doctor', 'patient']);
        return view('admin.appointments.show', compact('appointment'));
    }

    public function edit(AppointmentBooking $appointment)
    {
        $appointment->load(['schedule.doctor', 'patient']);
        $statuses = ['pending', 'approved', 'rejected', 'completed', 'cancelled'];

        return view('admin.appointments.edit', compact('appointment', 'statuses'));

    }

    public function update(Request $request, AppointmentBooking $appointment)
    {
        $validated = $request->validate([
            'status' => 'required|in:pending,approved,rejected,completed,cancelled',
            'patient_notes' => 'nullable|string|max:1000',
        ]);

        $appointment->update($validated);

        return redirect()->route('admin.appointments.index')
            ->with('success', 'Appointment updated successfully!');
    }

    public function destroy(AppointmentBooking $appointment)
    {
        $patientName = $appointment->patient->name ?? 'Unknown';
        $appointment->delete();

        return redirect()->route('admin.appointments.index')
            ->with('success', "Appointment for {$patientName} deleted successfully!");
    }
}
