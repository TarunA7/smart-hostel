import React, { useState, useEffect, createContext, useContext } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      // Verify token validity
      checkAuthStatus();
    } else {
      setLoading(false);
    }
  }, [token]);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Auth check failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (username, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, {
        username,
        password
      });
      
      const { access_token, user: userData } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(userData);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Login failed' 
      };
    }
  };

  const register = async (userData) => {
    try {
      const response = await axios.post(`${API}/auth/register`, userData);
      
      const { access_token, user: newUser } = response.data;
      
      localStorage.setItem('token', access_token);
      setToken(access_token);
      setUser(newUser);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      return { success: true };
    } catch (error) {
      console.error('Registration failed:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || 'Registration failed' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    login,
    register,
    logout,
    loading
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Login Component
const LoginForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [formData, setFormData] = useState({
    username: '',
    password: '',
    email: '',
    full_name: '',
    phone: '',
    student_id: '',
    role: 'student'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      let result;
      if (isLogin) {
        result = await login(formData.username, formData.password);
      } else {
        result = await register(formData);
      }

      if (!result.success) {
        setError(result.error);
      }
    } catch (error) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-blue-600 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="flex justify-center">
            <img 
              src="https://images.unsplash.com/photo-1574275639052-4655b340a669?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzV8MHwxfHNlYXJjaHwyfHxzdHVkZW50JTIwYWNjb21tb2RhdGlvbnxlbnwwfHx8Ymx1ZXwxNzUzNTI0MTc1fDA&ixlib=rb-4.1.0&q=85"
              alt="Logo"
              className="h-16 w-16 rounded-full"
            />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-white">
            {isLogin ? 'Sign in to your account' : 'Create your account'}
          </h2>
          <p className="mt-2 text-center text-sm text-blue-100">
            Smart Hostel Management System
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm space-y-4">
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-white mb-1">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your username"
                value={formData.username}
                onChange={handleChange}
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white mb-1">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                placeholder="Enter your password"
                value={formData.password}
                onChange={handleChange}
              />
            </div>

            {!isLogin && (
              <>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-white mb-1">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    required
                    className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="Enter your email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-white mb-1">
                    Full Name
                  </label>
                  <input
                    id="full_name"
                    name="full_name"
                    type="text"
                    required
                    className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="Enter your full name"
                    value={formData.full_name}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="phone" className="block text-sm font-medium text-white mb-1">
                    Phone (Optional)
                  </label>
                  <input
                    id="phone"
                    name="phone"
                    type="tel"
                    className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    placeholder="Enter your phone number"
                    value={formData.phone}
                    onChange={handleChange}
                  />
                </div>

                <div>
                  <label htmlFor="role" className="block text-sm font-medium text-white mb-1">
                    Role
                  </label>
                  <select
                    id="role"
                    name="role"
                    required
                    className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                    value={formData.role}
                    onChange={handleChange}
                  >
                    <option value="student">Student</option>
                    <option value="warden">Warden</option>
                  </select>
                </div>

                {formData.role === 'student' && (
                  <div>
                    <label htmlFor="student_id" className="block text-sm font-medium text-white mb-1">
                      Student ID
                    </label>
                    <input
                      id="student_id"
                      name="student_id"
                      type="text"
                      required
                      className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm"
                      placeholder="Enter your student ID"
                      value={formData.student_id}
                      onChange={handleChange}
                    />
                  </div>
                )}
              </>
            )}
          </div>

          {error && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative">
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading ? 'Loading...' : (isLogin ? 'Sign in' : 'Sign up')}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-blue-100 hover:text-white"
            >
              {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main App Component
const App = () => {
  const { user, loading, logout } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState(null);
  const [students, setStudents] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [visitors, setVisitors] = useState([]);
  const [maintenance, setMaintenance] = useState([]);
  const [fees, setFees] = useState([]);
  const [movements, setMovements] = useState([]);
  const [appLoading, setAppLoading] = useState(false);

  // Form states
  const [studentForm, setStudentForm] = useState({
    name: '', email: '', phone: '', student_id: ''
  });
  const [roomForm, setRoomForm] = useState({
    room_number: '', floor: '', capacity: ''
  });
  const [visitorForm, setVisitorForm] = useState({
    name: '', phone: '', visiting_student_id: '', visiting_student_name: '', purpose: ''
  });
  const [maintenanceForm, setMaintenanceForm] = useState({
    student_id: '', student_name: '', room_number: '', issue_type: '', description: ''
  });
  const [feeForm, setFeeForm] = useState({
    student_id: '', student_name: '', fee_type: '', amount: '', due_date: ''
  });
  const [movementForm, setMovementForm] = useState({
    student_id: '', student_name: '', action: '', note: ''
  });

  // Load dashboard stats
  const loadStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  // Load students
  const loadStudents = async () => {
    try {
      const response = await axios.get(`${API}/students`);
      setStudents(response.data);
    } catch (error) {
      console.error('Error loading students:', error);
    }
  };

  // Load rooms
  const loadRooms = async () => {
    try {
      const response = await axios.get(`${API}/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error('Error loading rooms:', error);
    }
  };

  // Load visitors
  const loadVisitors = async () => {
    try {
      const response = await axios.get(`${API}/visitors`);
      setVisitors(response.data);
    } catch (error) {
      console.error('Error loading visitors:', error);
    }
  };

  // Load maintenance requests
  const loadMaintenance = async () => {
    try {
      const response = await axios.get(`${API}/maintenance`);
      setMaintenance(response.data);
    } catch (error) {
      console.error('Error loading maintenance:', error);
    }
  };

  // Load fees
  const loadFees = async () => {
    try {
      const response = await axios.get(`${API}/fees`);
      setFees(response.data);
    } catch (error) {
      console.error('Error loading fees:', error);
    }
  };

  // Load movements
  const loadMovements = async () => {
    try {
      const response = await axios.get(`${API}/movements/recent`);
      setMovements(response.data);
    } catch (error) {
      console.error('Error loading movements:', error);
    }
  };

  // Create student
  const createStudent = async (e) => {
    e.preventDefault();
    try {
      setAppLoading(true);
      await axios.post(`${API}/students`, studentForm);
      setStudentForm({ name: '', email: '', phone: '', student_id: '' });
      loadStudents();
      loadStats();
    } catch (error) {
      console.error('Error creating student:', error);
    } finally {
      setAppLoading(false);
    }
  };

  // Create room
  const createRoom = async (e) => {
    e.preventDefault();
    try {
      setAppLoading(true);
      await axios.post(`${API}/rooms`, {
        ...roomForm,
        floor: parseInt(roomForm.floor),
        capacity: parseInt(roomForm.capacity)
      });
      setRoomForm({ room_number: '', floor: '', capacity: '' });
      loadRooms();
      loadStats();
    } catch (error) {
      console.error('Error creating room:', error);
    } finally {
      setAppLoading(false);
    }
  };

  // Create visitor
  const createVisitor = async (e) => {
    e.preventDefault();
    try {
      setAppLoading(true);
      await axios.post(`${API}/visitors`, visitorForm);
      setVisitorForm({ name: '', phone: '', visiting_student_id: '', visiting_student_name: '', purpose: '' });
      loadVisitors();
      loadStats();
    } catch (error) {
      console.error('Error creating visitor:', error);
    } finally {
      setAppLoading(false);
    }
  };

  // Create maintenance request
  const createMaintenanceRequest = async (e) => {
    e.preventDefault();
    try {
      setAppLoading(true);
      await axios.post(`${API}/maintenance`, maintenanceForm);
      setMaintenanceForm({ student_id: '', student_name: '', room_number: '', issue_type: '', description: '' });
      loadMaintenance();
      loadStats();
    } catch (error) {
      console.error('Error creating maintenance request:', error);
    } finally {
      setAppLoading(false);
    }
  };

  // Create fee record
  const createFeeRecord = async (e) => {
    e.preventDefault();
    try {
      setAppLoading(true);
      await axios.post(`${API}/fees`, {
        ...feeForm,
        amount: parseFloat(feeForm.amount),
        due_date: new Date(feeForm.due_date).toISOString()
      });
      setFeeForm({ student_id: '', student_name: '', fee_type: '', amount: '', due_date: '' });
      loadFees();
      loadStats();
    } catch (error) {
      console.error('Error creating fee record:', error);
    } finally {
      setAppLoading(false);
    }
  };

  // Log movement
  const logMovement = async (e) => {
    e.preventDefault();
    try {
      setAppLoading(true);
      await axios.post(`${API}/movements`, movementForm);
      setMovementForm({ student_id: '', student_name: '', action: '', note: '' });
      loadMovements();
      loadStats();
      loadStudents();
    } catch (error) {
      console.error('Error logging movement:', error);
    } finally {
      setAppLoading(false);
    }
  };

  // Checkout visitor
  const checkoutVisitor = async (visitorId) => {
    try {
      await axios.post(`${API}/visitors/${visitorId}/checkout`);
      loadVisitors();
      loadStats();
    } catch (error) {
      console.error('Error checking out visitor:', error);
    }
  };

  // Pay fee
  const payFee = async (feeId) => {
    try {
      await axios.post(`${API}/fees/${feeId}/pay`);
      loadFees();
      loadStats();
    } catch (error) {
      console.error('Error paying fee:', error);
    }
  };

  // Allocate room
  const allocateRoom = async (roomId, studentId) => {
    try {
      await axios.post(`${API}/rooms/${roomId}/allocate/${studentId}`);
      loadRooms();
      loadStudents();
      loadStats();
    } catch (error) {
      console.error('Error allocating room:', error);
    }
  };

  useEffect(() => {
    if (user) {
      loadStats();
      loadStudents();
      loadRooms();
      loadVisitors();
      loadMaintenance();
      loadFees();
      loadMovements();
    }
  }, [user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginForm />;
  }

  const renderDashboard = () => (
    <div className="space-y-6">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg overflow-hidden">
        <div className="absolute inset-0 bg-black opacity-50"></div>
        <div className="relative px-8 py-12">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Smart Hostel Management</h1>
              <p className="text-xl text-blue-100">
                Welcome back, {user.full_name} ({user.role})
              </p>
            </div>
            <div className="hidden md:block">
              <img 
                src="https://images.unsplash.com/photo-1646669089665-85f3a5ee14be?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwxfHxob3N0ZWwlMjBtYW5hZ2VtZW50fGVufDB8fHxibHVlfDE3NTM1MjQxNzB8MA&ixlib=rb-4.1.0&q=85"
                alt="Hostel Building"
                className="w-32 h-32 rounded-lg object-cover"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                {stats.students_in}
              </div>
              <div className="ml-4">
                <p className="text-gray-600">Students In</p>
                <p className="text-2xl font-bold">{stats.students_in}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center text-white font-bold">
                {stats.students_out}
              </div>
              <div className="ml-4">
                <p className="text-gray-600">Students Out</p>
                <p className="text-2xl font-bold">{stats.students_out}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white font-bold">
                {stats.available_rooms}
              </div>
              <div className="ml-4">
                <p className="text-gray-600">Available Rooms</p>
                <p className="text-2xl font-bold">{stats.available_rooms}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-yellow-500 rounded-full flex items-center justify-center text-white font-bold">
                {stats.pending_maintenance}
              </div>
              <div className="ml-4">
                <p className="text-gray-600">Pending Maintenance</p>
                <p className="text-2xl font-bold">{stats.pending_maintenance}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                {stats.active_visitors}
              </div>
              <div className="ml-4">
                <p className="text-gray-600">Active Visitors</p>
                <p className="text-2xl font-bold">{stats.active_visitors}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {movements.slice(0, 5).map((movement) => (
            <div key={movement.id} className="flex items-center justify-between py-2 border-b">
              <div className="flex items-center space-x-3">
                <div className={`w-3 h-3 rounded-full ${movement.action === 'check_in' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="font-medium">{movement.student_name}</span>
                <span className="text-gray-600">{movement.action === 'check_in' ? 'checked in' : 'checked out'}</span>
              </div>
              <span className="text-sm text-gray-500">
                {new Date(movement.timestamp).toLocaleString()}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderStudents = () => (
    <div className="space-y-6">
      {user.role === 'warden' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Add New Student</h2>
          <form onSubmit={createStudent} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Student Name"
              value={studentForm.name}
              onChange={(e) => setStudentForm({...studentForm, name: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="email"
              placeholder="Email"
              value={studentForm.email}
              onChange={(e) => setStudentForm({...studentForm, email: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="tel"
              placeholder="Phone"
              value={studentForm.phone}
              onChange={(e) => setStudentForm({...studentForm, phone: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Student ID"
              value={studentForm.student_id}
              onChange={(e) => setStudentForm({...studentForm, student_id: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <button
              type="submit"
              disabled={appLoading}
              className="md:col-span-2 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {appLoading ? 'Adding...' : 'Add Student'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Students List</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student ID</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Room</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {students.map((student) => (
                <tr key={student.id}>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{student.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{student.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{student.phone}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{student.student_id}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{student.room_number || 'Not assigned'}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      student.status === 'in' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {student.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderRooms = () => (
    <div className="space-y-6">
      {user.role === 'warden' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Add New Room</h2>
          <form onSubmit={createRoom} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Room Number"
              value={roomForm.room_number}
              onChange={(e) => setRoomForm({...roomForm, room_number: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="number"
              placeholder="Floor"
              value={roomForm.floor}
              onChange={(e) => setRoomForm({...roomForm, floor: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="number"
              placeholder="Capacity"
              value={roomForm.capacity}
              onChange={(e) => setRoomForm({...roomForm, capacity: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <button
              type="submit"
              disabled={appLoading}
              className="md:col-span-3 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {appLoading ? 'Adding...' : 'Add Room'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Rooms List</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rooms.map((room) => (
            <div key={room.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold">Room {room.room_number}</h3>
                  <p className="text-gray-600">Floor {room.floor}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  room.status === 'available' ? 'bg-green-100 text-green-800' :
                  room.status === 'occupied' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {room.status}
                </span>
              </div>
              <div className="mb-3">
                <p className="text-sm text-gray-600">Occupancy: {room.occupied}/{room.capacity}</p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                  <div 
                    className="bg-blue-600 h-2 rounded-full" 
                    style={{ width: `${(room.occupied / room.capacity) * 100}%` }}
                  ></div>
                </div>
              </div>
              {user.role === 'warden' && room.status === 'available' && room.occupied < room.capacity && (
                <div className="mt-3">
                  <select 
                    className="w-full p-2 border rounded mb-2"
                    onChange={(e) => e.target.value && allocateRoom(room.id, e.target.value)}
                  >
                    <option value="">Select student to allocate</option>
                    {students.filter(s => !s.room_number).map(student => (
                      <option key={student.id} value={student.id}>{student.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderVisitors = () => (
    <div className="space-y-6">
      {user.role === 'warden' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Register New Visitor</h2>
          <form onSubmit={createVisitor} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Visitor Name"
              value={visitorForm.name}
              onChange={(e) => setVisitorForm({...visitorForm, name: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="tel"
              placeholder="Phone"
              value={visitorForm.phone}
              onChange={(e) => setVisitorForm({...visitorForm, phone: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Visiting Student ID"
              value={visitorForm.visiting_student_id}
              onChange={(e) => setVisitorForm({...visitorForm, visiting_student_id: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Visiting Student Name"
              value={visitorForm.visiting_student_name}
              onChange={(e) => setVisitorForm({...visitorForm, visiting_student_name: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Purpose of Visit"
              value={visitorForm.purpose}
              onChange={(e) => setVisitorForm({...visitorForm, purpose: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 md:col-span-2"
              required
            />
            <button
              type="submit"
              disabled={appLoading}
              className="md:col-span-2 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {appLoading ? 'Registering...' : 'Register Visitor'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Visitors List</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Visiting</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Purpose</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Check In</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                {user.role === 'warden' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {visitors.map((visitor) => (
                <tr key={visitor.id}>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{visitor.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{visitor.phone}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{visitor.visiting_student_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{visitor.purpose}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {new Date(visitor.check_in).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      visitor.status === 'checked_in' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {visitor.status}
                    </span>
                  </td>
                  {user.role === 'warden' && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      {visitor.status === 'checked_in' && (
                        <button
                          onClick={() => checkoutVisitor(visitor.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Check Out
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderMaintenance = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Create Maintenance Request</h2>
        <form onSubmit={createMaintenanceRequest} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Student ID"
            value={maintenanceForm.student_id}
            onChange={(e) => setMaintenanceForm({...maintenanceForm, student_id: e.target.value})}
            className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
          <input
            type="text"
            placeholder="Student Name"
            value={maintenanceForm.student_name}
            onChange={(e) => setMaintenanceForm({...maintenanceForm, student_name: e.target.value})}
            className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
          <input
            type="text"
            placeholder="Room Number"
            value={maintenanceForm.room_number}
            onChange={(e) => setMaintenanceForm({...maintenanceForm, room_number: e.target.value})}
            className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          />
          <select
            value={maintenanceForm.issue_type}
            onChange={(e) => setMaintenanceForm({...maintenanceForm, issue_type: e.target.value})}
            className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            required
          >
            <option value="">Select Issue Type</option>
            <option value="plumbing">Plumbing</option>
            <option value="electrical">Electrical</option>
            <option value="furniture">Furniture</option>
            <option value="cleaning">Cleaning</option>
            <option value="other">Other</option>
          </select>
          <textarea
            placeholder="Description"
            value={maintenanceForm.description}
            onChange={(e) => setMaintenanceForm({...maintenanceForm, description: e.target.value})}
            className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 md:col-span-2"
            rows="3"
            required
          />
          <button
            type="submit"
            disabled={appLoading}
            className="md:col-span-2 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {appLoading ? 'Creating...' : 'Create Request'}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Maintenance Requests</h2>
        <div className="space-y-4">
          {maintenance.map((request) => (
            <div key={request.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="text-lg font-semibold">{request.issue_type}</h3>
                  <p className="text-gray-600">Room {request.room_number} - {request.student_name}</p>
                </div>
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  request.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                  request.status === 'in_progress' ? 'bg-blue-100 text-blue-800' :
                  'bg-green-100 text-green-800'
                }`}>
                  {request.status}
                </span>
              </div>
              <p className="text-gray-700 mb-3">{request.description}</p>
              <p className="text-sm text-gray-500">
                Created: {new Date(request.created_at).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderFees = () => (
    <div className="space-y-6">
      {user.role === 'warden' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Create Fee Record</h2>
          <form onSubmit={createFeeRecord} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Student ID"
              value={feeForm.student_id}
              onChange={(e) => setFeeForm({...feeForm, student_id: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Student Name"
              value={feeForm.student_name}
              onChange={(e) => setFeeForm({...feeForm, student_name: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <select
              value={feeForm.fee_type}
              onChange={(e) => setFeeForm({...feeForm, fee_type: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select Fee Type</option>
              <option value="hostel_fee">Hostel Fee</option>
              <option value="mess_fee">Mess Fee</option>
              <option value="electricity">Electricity</option>
              <option value="water">Water</option>
              <option value="maintenance">Maintenance</option>
            </select>
            <input
              type="number"
              step="0.01"
              placeholder="Amount"
              value={feeForm.amount}
              onChange={(e) => setFeeForm({...feeForm, amount: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="date"
              placeholder="Due Date"
              value={feeForm.due_date}
              onChange={(e) => setFeeForm({...feeForm, due_date: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 md:col-span-2"
              required
            />
            <button
              type="submit"
              disabled={appLoading}
              className="md:col-span-2 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {appLoading ? 'Creating...' : 'Create Fee Record'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Fee Records</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fee Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Due Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                {user.role === 'warden' && (
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                )}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {fees.map((fee) => (
                <tr key={fee.id}>
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{fee.student_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">{fee.fee_type}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">${fee.amount}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-600">
                    {new Date(fee.due_date).toLocaleDateString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                      fee.status === 'paid' ? 'bg-green-100 text-green-800' :
                      fee.status === 'overdue' ? 'bg-red-100 text-red-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>
                      {fee.status}
                    </span>
                  </td>
                  {user.role === 'warden' && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      {fee.status !== 'paid' && (
                        <button
                          onClick={() => payFee(fee.id)}
                          className="bg-green-600 text-white px-3 py-1 rounded text-sm hover:bg-green-700"
                        >
                          Mark Paid
                        </button>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderMovements = () => (
    <div className="space-y-6">
      {user.role === 'warden' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold mb-4">Log Student Movement</h2>
          <form onSubmit={logMovement} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <input
              type="text"
              placeholder="Student ID"
              value={movementForm.student_id}
              onChange={(e) => setMovementForm({...movementForm, student_id: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <input
              type="text"
              placeholder="Student Name"
              value={movementForm.student_name}
              onChange={(e) => setMovementForm({...movementForm, student_name: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            />
            <select
              value={movementForm.action}
              onChange={(e) => setMovementForm({...movementForm, action: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              required
            >
              <option value="">Select Action</option>
              <option value="check_in">Check In</option>
              <option value="check_out">Check Out</option>
            </select>
            <input
              type="text"
              placeholder="Note (optional)"
              value={movementForm.note}
              onChange={(e) => setMovementForm({...movementForm, note: e.target.value})}
              className="p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
            <button
              type="submit"
              disabled={appLoading}
              className="md:col-span-2 bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {appLoading ? 'Logging...' : 'Log Movement'}
            </button>
          </form>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-bold mb-4">Movement History</h2>
        <div className="space-y-4">
          {movements.map((movement) => (
            <div key={movement.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div className="flex items-center space-x-3">
                  <div className={`w-4 h-4 rounded-full ${movement.action === 'check_in' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                  <div>
                    <h3 className="font-semibold">{movement.student_name}</h3>
                    <p className="text-gray-600">{movement.action === 'check_in' ? 'Checked In' : 'Checked Out'}</p>
                    {movement.note && <p className="text-sm text-gray-500">{movement.note}</p>}
                  </div>
                </div>
                <span className="text-sm text-gray-500">
                  {new Date(movement.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'students', label: 'Students', icon: '👥' },
    { id: 'rooms', label: 'Rooms', icon: '🏠' },
    { id: 'visitors', label: 'Visitors', icon: '🚪' },
    { id: 'maintenance', label: 'Maintenance', icon: '🔧' },
    { id: 'fees', label: 'Fees', icon: '💰' },
    { id: 'movements', label: 'In/Out', icon: '🚶' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <img 
                src="https://images.unsplash.com/photo-1574275639052-4655b340a669?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzV8MHwxfHNlYXJjaHwyfHxzdHVkZW50JTIwYWNjb21tb2RhdGlvbnxlbnwwfHx8Ymx1ZXwxNzUzNTI0MTc1fDA&ixlib=rb-4.1.0&q=85"
                alt="Logo"
                className="h-8 w-8 rounded-full mr-3"
              />
              <h1 className="text-xl font-bold text-gray-800">Smart Hostel</h1>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex space-x-1">
                {tabs.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      activeTab === tab.id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                    }`}
                  >
                    <span className="mr-2">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  {user.full_name} ({user.role})
                </span>
                <button
                  onClick={logout}
                  className="text-red-600 hover:text-red-700 text-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'dashboard' && renderDashboard()}
        {activeTab === 'students' && renderStudents()}
        {activeTab === 'rooms' && renderRooms()}
        {activeTab === 'visitors' && renderVisitors()}
        {activeTab === 'maintenance' && renderMaintenance()}
        {activeTab === 'fees' && renderFees()}
        {activeTab === 'movements' && renderMovements()}
      </main>
    </div>
  );
};

const MainApp = () => {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
};

export default MainApp;