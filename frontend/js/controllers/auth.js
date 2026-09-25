(function () {
  'use strict';

  var app = angular.module('cinemaApp');

  app.controller('LoginCtrl', ['$location', 'Auth', 'Notify', 'ApiError', function ($location, Auth, Notify, ApiError) {
    var vm = this;
    vm.form = {};
    vm.expired = !!$location.search().expired;
    // Seeded accounts (backend/app/seed.py), shown to make manual testing quick.
    vm.demoAccounts = [
      { label: 'Admin', email: 'admin@cinema.example.com' },
      { label: 'Nhân viên', email: 'staff@cinema.example.com' },
      { label: 'Khách hàng', email: 'customer@cinema.example.com' }
    ];

    vm.useDemo = function (account) {
      vm.form = { email: account.email, password: 'Cinema@123' };
    };

    vm.submit = function () {
      vm.error = null;
      vm.loading = true;
      Auth.login(vm.form.email, vm.form.password).then(function (user) {
        Notify.success('Xin chào, ' + user.full_name + '!');
        var next = $location.search().next;
        $location.url(next && next.charAt(0) === '/' ? next : Auth.homePath());
      }, function (res) {
        vm.error = ApiError.message(res);
      }).finally(function () {
        vm.loading = false;
      });
    };
  }]);

  app.controller('RegisterCtrl', ['$http', '$location', 'API', 'Auth', 'Notify', 'ApiError',
    function ($http, $location, API, Auth, Notify, ApiError) {
      var vm = this;
      vm.form = {};

      vm.submit = function () {
        vm.error = null;
        if (vm.form.password !== vm.form.confirm) {
          vm.error = 'Mật khẩu nhập lại không khớp';
          return;
        }
        vm.loading = true;
        var body = {
          full_name: vm.form.full_name,
          email: vm.form.email,
          phone: vm.form.phone || null,
          password: vm.form.password
        };
        $http.post(API + '/auth/register', body).then(function () {
          return Auth.login(body.email, body.password);
        }).then(function () {
          Notify.success('Đăng ký thành công. Chào mừng bạn!');
          $location.url(Auth.homePath());
        }, function (res) {
          vm.error = ApiError.message(res);
        }).finally(function () {
          vm.loading = false;
        });
      };
    }
  ]);

  app.controller('ForgotPasswordCtrl', ['$http', 'API', 'ApiError', function ($http, API, ApiError) {
    var vm = this;
    vm.form = {};
    vm.mailhogUrl = window.APP_CONFIG.mailhogUrl;

    vm.submit = function () {
      vm.error = null;
      vm.loading = true;
      $http.post(API + '/auth/forgot-password', vm.form).then(function (res) {
        vm.sent = res.data.message;
      }, function (res) {
        vm.error = ApiError.message(res);
      }).finally(function () {
        vm.loading = false;
      });
    };
  }]);

  app.controller('ResetPasswordCtrl', ['$http', '$location', 'API', 'Auth', 'Notify', 'ApiError',
    function ($http, $location, API, Auth, Notify, ApiError) {
      var vm = this;
      vm.token = $location.search().token;
      vm.form = {};

      vm.submit = function () {
        vm.error = null;
        if (vm.form.password !== vm.form.confirm) {
          vm.error = 'Mật khẩu nhập lại không khớp';
          return;
        }
        vm.loading = true;
        $http.post(API + '/auth/reset-password', { token: vm.token, new_password: vm.form.password })
          .then(function () {
            Auth.clear();  // the reset revoked every existing session anyway
            Notify.success('Đã đặt lại mật khẩu. Vui lòng đăng nhập bằng mật khẩu mới.');
            $location.url('/login');
          }, function (res) {
            vm.error = ApiError.message(res);
          }).finally(function () {
            vm.loading = false;
          });
      };
    }
  ]);
})();
