(function () {
  'use strict';

  var app = angular.module('cinemaApp');

  // Session = tokens + current user, persisted in localStorage.
  app.factory('Auth', ['$http', '$q', 'API', function ($http, $q, API) {
    var KEY = 'cinema.session';
    var session = read();
    var refreshing = null;

    function read() {
      try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; }
    }

    function write() {
      try {
        if (session) localStorage.setItem(KEY, JSON.stringify(session));
        else localStorage.removeItem(KEY);
      } catch (e) { /* storage blocked: session lives in memory only */ }
    }

    var Auth = {
      user: function () { return session && session.user; },
      accessToken: function () { return session && session.access; },
      isLoggedIn: function () { return !!(session && session.access && session.user); },
      hasRole: function (roles) {
        var user = Auth.user();
        return !!user && roles.indexOf(user.role) !== -1;
      },
      homePath: function () {
        var user = Auth.user();
        if (!user) return '/';
        return { admin: '/admin', staff: '/staff' }[user.role] || '/';
      },

      login: function (email, password) {
        return $http.post(API + '/auth/login', { email: email, password: password }).then(function (res) {
          session = { access: res.data.access_token, refresh: res.data.refresh_token, user: null };
          return Auth.fetchMe();
        }).catch(function (err) {
          Auth.clear();
          return $q.reject(err);
        });
      },

      fetchMe: function () {
        return $http.get(API + '/users/me').then(function (res) {
          Auth.setUser(res.data);
          return res.data;
        });
      },

      setUser: function (user) {
        if (!session) return;
        session.user = user;
        write();
      },

      // Single-flight: parallel 401s share one refresh call.
      refresh: function () {
        if (!session || !session.refresh) return $q.reject();
        if (!refreshing) {
          refreshing = $http.post(API + '/auth/refresh', { refresh_token: session.refresh }, { skipAuth: true })
            .then(function (res) {
              session.access = res.data.access_token;
              session.refresh = res.data.refresh_token;
              write();
            })
            .finally(function () { refreshing = null; });
        }
        return refreshing;
      },

      logout: function () {
        var request = session ? $http.post(API + '/auth/logout').catch(angular.noop) : $q.resolve();
        return request.finally(Auth.clear);
      },

      clear: function () {
        session = null;
        write();
      }
    };
    return Auth;
  }]);

  // Adds the bearer token; on 401 refreshes once and replays the request, else sends the user to login.
  app.factory('authInterceptor', ['$q', '$injector', 'API', function ($q, $injector, API) {
    function isApi(url) { return (url || '').indexOf(API) === 0; }

    function sessionExpired() {
      $injector.get('Auth').clear();
      var $location = $injector.get('$location');
      if ($location.path() !== '/login') $location.url('/login?expired=1');
    }

    return {
      request: function (config) {
        var token = $injector.get('Auth').accessToken();
        if (isApi(config.url) && token && !config.skipAuth) {
          config.headers.Authorization = 'Bearer ' + token;
        }
        return config;
      },

      responseError: function (res) {
        var config = res.config || {};
        var Auth = $injector.get('Auth');
        var canRetry = res.status === 401 && isApi(config.url) && !config.skipAuth && !config.retried &&
          Auth.accessToken() && !/\/auth\/(login|refresh)$/.test(config.url);

        if (canRetry) {
          return Auth.refresh().then(function () {
            config.retried = true;
            return $injector.get('$http')(config);
          }, function () {
            sessionExpired();
            return $q.reject(res);
          });
        }
        if (res.status === 401 && config.retried) sessionExpired();
        return $q.reject(res);
      }
    };
  }]);

  // Turns API error responses into a Vietnamese message for the user.
  app.factory('ApiError', function () {
    var LABELS = {
      email: 'Email', password: 'Mật khẩu', new_password: 'Mật khẩu mới', current_password: 'Mật khẩu hiện tại',
      full_name: 'Họ tên', phone: 'Số điện thoại', role: 'Vai trò', cinema_id: 'Rạp'
    };

    function validationMessage(error) {
      var field = error.loc[error.loc.length - 1];
      var label = LABELS[field] || field;
      var ctx = error.ctx || {};
      switch (error.type) {
        case 'missing': return 'Vui lòng nhập ' + label.toLowerCase();
        case 'string_too_short': return label + ' phải có ít nhất ' + ctx.min_length + ' ký tự';
        case 'string_too_long': return label + ' tối đa ' + ctx.max_length + ' ký tự';
        case 'string_pattern_mismatch':
          return field === 'phone' ? 'Số điện thoại không hợp lệ (9–15 chữ số)' : label + ' không hợp lệ';
      }
      if (field === 'email') return 'Email không hợp lệ';
      return error.msg.replace(/^Value error, /, '');
    }

    return {
      message: function (res) {
        if (!res || res.status <= 0) return 'Không kết nối được máy chủ. Vui lòng thử lại.';
        var detail = res.data && res.data.detail;
        if (detail && detail.message) return detail.message;
        if (angular.isArray(detail) && detail.length) return validationMessage(detail[0]);
        if (res.status === 403) return 'Bạn không có quyền thực hiện thao tác này';
        return 'Đã có lỗi xảy ra (mã ' + res.status + ')';
      },
      code: function (res) {
        return res && res.data && res.data.detail && res.data.detail.code;
      }
    };
  });

  app.factory('Notify', ['$timeout', function ($timeout) {
    var items = [];

    function remove(item) {
      var i = items.indexOf(item);
      if (i !== -1) items.splice(i, 1);
    }

    function push(type, text) {
      var item = { type: type, text: text };
      items.push(item);
      if (items.length > 3) items.shift();  // keep the stack short
      $timeout(function () { remove(item); }, 4000);
    }

    return {
      items: items,
      remove: remove,
      success: function (text) { push('success', text); },
      error: function (text) { push('error', text); }
    };
  }]);

  // Cinemas change rarely: fetch once per page load.
  app.factory('Cinemas', ['$http', 'API', function ($http, API) {
    var cache = null;
    return {
      list: function () {
        if (!cache) {
          cache = $http.get(API + '/cinemas').then(function (res) { return res.data; });
          cache.catch(function () { cache = null; });
        }
        return cache;
      }
    };
  }]);
})();
