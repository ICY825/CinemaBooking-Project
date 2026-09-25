(function () {
  'use strict';

  var ALL_ROLES = ['customer', 'staff', 'admin'];

  function route(template, controller, extra) {
    return angular.extend({
      templateUrl: 'views/' + template + '.html',
      controller: controller,
      controllerAs: 'vm'
    }, extra);
  }

  angular.module('cinemaApp', ['ngRoute'])
    .constant('API', window.APP_CONFIG.apiBase)
    .constant('ROLE_LABELS', { customer: 'Khách hàng', staff: 'Nhân viên', admin: 'Quản trị' })
    // Sidebar per role. Paths under /soon/ are features scheduled for later weeks (see UPCOMING).
    .constant('MENUS', {
      customer: [
        { path: '/', label: 'Trang chủ' },
        { path: '/soon/movies', label: 'Phim & lịch chiếu' },
        { path: '/soon/my-tickets', label: 'Vé của tôi' },
        { path: '/profile', label: 'Hồ sơ' }
      ],
      staff: [
        { path: '/staff', label: 'Bảng điều khiển' },
        { path: '/soon/pos', label: 'Bán vé tại quầy' },
        { path: '/soon/checkin', label: 'Soát vé QR' },
        { path: '/profile', label: 'Hồ sơ' }
      ],
      admin: [
        { path: '/admin', label: 'Tổng quan' },
        { path: '/admin/users', label: 'Tài khoản' },
        { path: '/soon/movies', label: 'Phim' },
        { path: '/soon/cinemas', label: 'Rạp & sơ đồ ghế' },
        { path: '/soon/showtimes', label: 'Suất chiếu & giá vé' },
        { path: '/soon/reports', label: 'Báo cáo doanh thu' },
        { path: '/profile', label: 'Hồ sơ' }
      ]
    })
    .constant('UPCOMING', {
      movies: { title: 'Danh mục phim & lịch chiếu', task: '2.1, 2.3, 3.3', when: 'Tuần 2–3 (28/09 – 11/10)' },
      cinemas: { title: 'Rạp, phòng chiếu & editor sơ đồ ghế', task: '2.2', when: 'Tuần 2 (29/09 – 30/09)' },
      showtimes: { title: 'Suất chiếu & bảng giá', task: '3.1, 3.2', when: 'Tuần 3 (05/10 – 06/10)' },
      'my-tickets': { title: 'Vé của tôi (QR, PDF, hoàn/đổi vé)', task: '5.2, 5.3', when: 'Tuần 5 (21/10 – 22/10)' },
      pos: { title: 'Bán vé tại quầy', task: '6.1', when: 'Tuần 6 (26/10 – 27/10)' },
      checkin: { title: 'Soát vé bằng QR', task: '6.2', when: 'Tuần 6 (28/10)' },
      reports: { title: 'Dashboard doanh thu', task: '7.1', when: 'Tuần 7 (02/11 – 03/11)' }
    })

    .config(['$routeProvider', '$httpProvider', function ($routeProvider, $httpProvider) {
      $httpProvider.interceptors.push('authInterceptor');

      $routeProvider
        .when('/', route('home', 'HomeCtrl'))
        .when('/login', route('login', 'LoginCtrl', { guestOnly: true }))
        .when('/register', route('register', 'RegisterCtrl', { guestOnly: true }))
        .when('/forgot-password', route('forgot-password', 'ForgotPasswordCtrl', { guestOnly: true }))
        .when('/reset-password', route('reset-password', 'ResetPasswordCtrl'))
        .when('/profile', route('profile', 'ProfileCtrl', { roles: ALL_ROLES }))
        .when('/staff', route('staff-dashboard', 'StaffDashboardCtrl', { roles: ['staff', 'admin'] }))
        .when('/admin', route('admin-dashboard', 'AdminDashboardCtrl', { roles: ['admin'] }))
        .when('/admin/users', route('admin-users', 'AdminUsersCtrl', { roles: ['admin'] }))
        .when('/soon/:feature', route('soon', 'SoonCtrl'))
        .when('/forbidden', { templateUrl: 'views/forbidden.html' })
        .otherwise('/');
    }])

    // Route guard: `roles` = must be logged in with one of these roles; `guestOnly` = login/register pages.
    .run(['$rootScope', '$location', 'Auth', function ($rootScope, $location, Auth) {
      $rootScope.$on('$routeChangeStart', function (event, next) {
        var target = next && next.$$route;
        if (!target) return;

        if (target.roles && !Auth.isLoggedIn()) {
          event.preventDefault();
          $location.url('/login?next=' + encodeURIComponent($location.url()));
        } else if (target.roles && !Auth.hasRole(target.roles)) {
          event.preventDefault();
          $location.url('/forbidden');
        } else if (target.guestOnly && Auth.isLoggedIn()) {
          event.preventDefault();
          $location.url(Auth.homePath());
        }
      });
    }]);
})();
