(function () {
  'use strict';

  angular.module('cinemaApp').controller('AdminUsersCtrl', [
    '$http', 'API', 'Auth', 'Cinemas', 'Notify', 'ApiError', 'ROLE_LABELS',
    function ($http, API, Auth, Cinemas, Notify, ApiError, ROLE_LABELS) {
      var vm = this;
      vm.roleLabels = ROLE_LABELS;
      vm.roles = ['customer', 'staff', 'admin'];
      vm.filters = { q: '', role: '', page: 1, size: 10 };
      vm.cinemas = [];

      Cinemas.list().then(function (cinemas) { vm.cinemas = cinemas; });

      vm.load = function () {
        vm.loading = true;
        var params = {
          q: vm.filters.q || undefined,
          role: vm.filters.role || undefined,
          page: vm.filters.page,
          size: vm.filters.size
        };
        $http.get(API + '/users', { params: params }).then(function (res) {
          vm.data = res.data;
        }, function (res) {
          Notify.error(ApiError.message(res));
        }).finally(function () {
          vm.loading = false;
        });
      };

      vm.search = function () {
        vm.filters.page = 1;
        vm.load();
      };

      vm.pageCount = function () {
        return vm.data ? Math.max(1, Math.ceil(vm.data.total / vm.filters.size)) : 1;
      };

      vm.goTo = function (page) {
        vm.filters.page = page;
        vm.load();
      };

      vm.cinemaName = function (id) {
        var cinema = vm.cinemas.filter(function (c) { return c.id === id; })[0];
        return cinema ? cinema.name : '';
      };

      vm.isSelf = function (user) {
        var me = Auth.user();  // null for a moment while logging out
        return !!me && user.id === me.id;
      };

      vm.openCreate = function () {
        vm.error = null;
        vm.editing = { mode: 'create', form: { role: 'staff', cinema_id: vm.cinemas.length ? vm.cinemas[0].id : null } };
      };

      vm.openEdit = function (user) {
        vm.error = null;
        vm.editing = {
          mode: 'edit',
          user: user,
          form: {
            full_name: user.full_name,
            phone: user.phone || '',
            role: user.role,
            is_active: user.is_active,
            cinema_id: user.cinema_id,
            row_version: user.row_version
          }
        };
      };

      vm.close = function () {
        vm.editing = null;
      };

      vm.save = function () {
        var form = angular.copy(vm.editing.form);
        form.phone = form.phone || null;
        if (form.role !== 'staff') form.cinema_id = null;  // only staff are scoped to a cinema

        var request = vm.editing.mode === 'create'
          ? $http.post(API + '/users', form)
          : $http.patch(API + '/users/' + vm.editing.user.id, form);

        vm.error = null;
        vm.saving = true;
        request.then(function (res) {
          Notify.success(vm.editing.mode === 'create' ? 'Đã tạo tài khoản ' + res.data.email : 'Đã cập nhật tài khoản');
          vm.editing = null;
          vm.load();
        }, function (res) {
          vm.error = ApiError.message(res);
          if (ApiError.code(res) === 'VERSION_CONFLICT') vm.load();
        }).finally(function () {
          vm.saving = false;
        });
      };

      vm.load();
    }
  ]);
})();
