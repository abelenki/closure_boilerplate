goog.provide('closure_boilerplate.urls');

goog.require('closure_boilerplate.handlers.LandingHandler');
goog.require('relief.handlers.errors');


/**
 * @type {!relief.nav.URLMap}
 */
closure_boilerplate.urls = {
  '': closure_boilerplate.handlers.LandingHandler,
  '/': closure_boilerplate.handlers.LandingHandler,

  ':401': relief.handlers.errors.Error401,
  ':404': relief.handlers.errors.Error404,
  ':501': relief.handlers.errors.Error501
};
