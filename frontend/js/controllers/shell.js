(function () {
  'use strict';

  angular.module('cinemaApp').controller('ShellCtrl', [
    '$location', 'Auth', 'Notify', 'MENUS', 'ROLE_LABELS',
    function ($location, Auth, Notify, MENUS, ROLE_LABELS) {
      var vm = this;
      var NO_MENU = [];

      vm.auth = Auth;
      vm.notify = Notify;
      vm.roleLabels = ROLE_LABELS;
      vm.sidebarOpen = false;

      vm.menu = function () {
        var user = Auth.user();
        return user ? MENUS[user.role] : NO_MENU;
      };

      vm.isActive = function (path) {
        return $location.path() === path;
      };

      vm.logout = function () {
        Auth.logout().then(function () {
          Notify.success('Đã đăng xuất');
          $location.url('/login');
        });
      };

      // Pick up changes an admin made to this account (role, lock) since the last visit.
      if (Auth.isLoggedIn()) Auth.fetchMe().catch(angular.noop);
    }
  ]);
})();
