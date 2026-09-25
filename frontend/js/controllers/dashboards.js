(function () {
  'use strict';

  var app = angular.module('cinemaApp');

  app.controller('HomeCtrl', ['Auth', function (Auth) {
    this.auth = Auth;
  }]);

  app.controller('SoonCtrl', ['$routeParams', 'UPCOMING', function ($routeParams, UPCOMING) {
    this.feature = UPCOMING[$routeParams.feature];
  }]);

  app.controller('StaffDashboardCtrl', ['Auth', 'Cinemas', function (Auth, Cinemas) {
    var vm = this;
    vm.user = Auth.user();
    Cinemas.list().then(function (cinemas) {
      var cinema = cinemas.filter(function (c) { return c.id === vm.user.cinema_id; })[0];
      vm.cinema = cinema;
    });
  }]);

  app.controller('AdminDashboardCtrl', ['$http', '$q', 'API', 'ROLE_LABELS', 'Cinemas',
    function ($http, $q, API, ROLE_LABELS, Cinemas) {
      var vm = this;
      vm.roleLabels = ROLE_LABELS;
      vm.counts = {};

      // One cheap request per role: size=1, only `total` is used.
      ['customer', 'staff', 'admin'].forEach(function (role) {
        $http.get(API + '/users', { params: { role: role, size: 1 } }).then(function (res) {
          vm.counts[role] = res.data.total;
        });
      });
      Cinemas.list().then(function (cinemas) { vm.cinemaCount = cinemas.length; });

      vm.roadmap = [
        { week: 'Tuần 1', dates: '21/09 – 27/09', scope: 'Nền tảng, tài khoản, phân quyền', done: true },
        { week: 'Tuần 2', dates: '28/09 – 04/10', scope: 'Danh mục phim, rạp, sơ đồ ghế' },
        { week: 'Tuần 3', dates: '05/10 – 11/10', scope: 'Suất chiếu, bảng giá, job nền' },
        { week: 'Tuần 4', dates: '12/10 – 18/10', scope: 'Chọn ghế, giữ ghế, chống đặt trùng (M1)' },
        { week: 'Tuần 5', dates: '19/10 – 25/10', scope: 'Thanh toán, vé QR/PDF, hoàn/đổi vé' },
        { week: 'Tuần 6', dates: '26/10 – 01/11', scope: 'Bán vé tại quầy, soát vé, thành viên' },
        { week: 'Tuần 7', dates: '02/11 – 08/11', scope: 'Báo cáo doanh thu, khuyến mãi (M2)' },
        { week: 'Tuần 8–9', dates: '09/11 – 20/11', scope: 'Kiểm thử tải, bảo mật, triển khai, bàn giao (M3)' }
      ];
    }
  ]);
})();
