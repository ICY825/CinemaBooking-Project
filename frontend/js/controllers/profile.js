(function () {
  'use strict';

  angular.module('cinemaApp').controller('ProfileCtrl', [
    '$http', '$location', 'API', 'Auth', 'Cinemas', 'Notify', 'ApiError', 'ROLE_LABELS',
    function ($http, $location, API, Auth, Cinemas, Notify, ApiError, ROLE_LABELS) {
      var vm = this;
      vm.roleLabels = ROLE_LABELS;
      vm.password = {};

      function show(user) {
        vm.user = user;
        vm.form = { full_name: user.full_name, phone: user.phone || '' };
        if (user.cinema_id) {
          Cinemas.list().then(function (cinemas) {
            var cinema = cinemas.filter(function (c) { return c.id === user.cinema_id; })[0];
            vm.cinemaName = cinema && cinema.name;
          });
        }
      }

      function load() {
        return Auth.fetchMe().then(show);
      }

      show(Auth.user());
      load();

      vm.saveProfile = function () {
        vm.profileError = null;
        vm.saving = true;
        var body = { full_name: vm.form.full_name, phone: vm.form.phone || null, row_version: vm.user.row_version };
        $http.patch(API + '/users/me', body).then(function (res) {
          Auth.setUser(res.data);
          show(res.data);
          Notify.success('Đã lưu hồ sơ');
        }, function (res) {
          vm.profileError = ApiError.message(res);
          if (ApiError.code(res) === 'VERSION_CONFLICT') load();
        }).finally(function () {
          vm.saving = false;
        });
      };

      vm.changePassword = function () {
        vm.passwordError = null;
        if (vm.password.new_password !== vm.password.confirm) {
          vm.passwordError = 'Mật khẩu nhập lại không khớp';
          return;
        }
        vm.changing = true;
        var body = { current_password: vm.password.current_password, new_password: vm.password.new_password };
        $http.post(API + '/users/me/change-password', body).then(function () {
          Auth.clear();  // every session was revoked by the server
          Notify.success('Đã đổi mật khẩu. Vui lòng đăng nhập lại.');
          $location.url('/login');
        }, function (res) {
          vm.passwordError = ApiError.message(res);
        }).finally(function () {
          vm.changing = false;
        });
      };
    }
  ]);
})();
