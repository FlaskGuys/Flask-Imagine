"""
Flask Imagine extension.
"""
import logging

from flask import current_app, abort, redirect

from .adapters import ImagineFilesystemAdapter
from .filters import *
from .helpers.regex_route import RegexConverter

LOGGER = logging.getLogger(__file__)


class Imagine(object):
    """
    Flask Imagine extension
    """
    adapters = {
        'fs': ImagineFilesystemAdapter
    }
    filters = {
        'autorotate': AutorotateFilter,
        'relative_resize': RelativeResizeFilter,
        'thumbnail': ThumbnailFilter
    }

    filter_sets = {}
    adapter = None

    def __init__(self, app=None):
        """
        :param app: Flask application
        :return:
        """
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        :param app: Flask application
        :return:
        """
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['imagine'] = self

        self._set_defaults(app)

        if isinstance(app.config['IMAGINE_ADAPTERS'], dict):
            self.filters.update(app.config['IMAGINE_ADAPTERS'])
        if isinstance(app.config['IMAGINE_FILTERS'], dict):
            self.filters.update(app.config['IMAGINE_FILTERS'])

        self._handle_adapter(app)
        self._handle_filter_sets(app)

        self._add_url_rule(app)
        self._add_template_filter(app)

    @classmethod
    def _set_defaults(cls, app):
        """
        Set default configuration parameters
        :param app: Flask application
        :return:
        """
        app.config.setdefault('IMAGINE_URL', '/media/cache/resolve')
        app.config.setdefault('IMAGINE_NAME', 'imagine')
        app.config.setdefault('IMAGINE_THUMBS_PATH', 'cache/')
        app.config.setdefault('IMAGINE_CACHE_ENABLED', True)

        app.config.setdefault('IMAGINE_ADAPTERS', {})
        app.config.setdefault('IMAGINE_FILTERS', {})

        app.config.setdefault('IMAGINE_ADAPTER', {
            'name': 'fs',
            'source_folder': '/static/',
            'cache_folder': '/cache/'
        })

        app.config.setdefault('IMAGINE_FILTER_SETS', {})

        return app

    def _handle_adapter(self, app):
        """
        Handle storage adapter configuration
        :param app: Flask application
        :return:
        """
        if 'IMAGINE_ADAPTER' in app.config \
                and 'name' in app.config['IMAGINE_ADAPTER'] \
                and app.config['IMAGINE_ADAPTER']['name'] in self.adapters.keys():
            self.adapter = self.adapters[app.config['IMAGINE_ADAPTER']['name']](
                **app.config['IMAGINE_ADAPTER']
            )
        else:
            raise ValueError('Unknown adapter: %s' % unicode(app.config['IMAGINE_ADAPTER']))

    def _handle_filter_sets(self, app):
        """
        Handle filter sets
        :param app: Flask application
        :return:
        """
        if 'IMAGINE_FILTER_SETS' in app.config and isinstance(app.config['IMAGINE_FILTER_SETS'], dict):
            for filter_name, filters_settings in app.config['IMAGINE_FILTER_SETS'].iteritems():
                filter_set = []
                if isinstance(filters_settings, dict) and 'filters' in filters_settings:
                    for filter_type, filter_settings in filters_settings['filters'].iteritems():
                        if filter_type in self.filters:
                            filter_item = self.filters[filter_type](**filter_settings)
                            if isinstance(filter_item, ImagineFilterInterface):
                                filter_set.append(filter_item)
                            else:
                                raise ValueError('Filter must be implement ImagineFilterInterface')
                        else:
                            raise ValueError('Unknown filter type: %s' % filter_type)

                    filter_config = {'filters': filter_set}
                    if 'cached' in filters_settings and filters_settings['cached']:
                        filter_config['cached'] = True
                    else:
                        filter_config['cached'] = False

                    self.filter_sets.update({filter_name: filter_config})
                else:
                    raise ValueError('Wrong settings for filter: %s' % filter_name)
        else:
            raise ValueError('Filters configuration does not present')

    def _add_url_rule(self, app):
        """
        Add url rule for get filtered images
        :param app: Flask application
        :return:
        """
        app.url_map.converters['regex'] = RegexConverter
        app.add_url_rule(
            app.config['IMAGINE_URL'] + '/<regex("[^\/]+"):filter_name>/<path:path>',
            app.config['IMAGINE_NAME'],
            self.handle_request
        )

        return app

    @classmethod
    def _add_template_filter(cls, app):
        """
        Add template filter
        :param app: Flask application
        :return:
        """
        if hasattr(app, 'add_template_filter'):
            app.add_template_filter(imagine_filter, 'imagine_filter')
        else:
            ctx = {
                'imagine_filter': imagine_filter
            }
            app.context_processor(lambda: ctx)  # pragma: no cover

        return app

    def handle_request(self, filter_name, path):
        """
        Handle image request
        :param filter_name: filter_name
        :param path: image_path
        :param kwargs:
        :return:
        """
        if filter_name in self.filter_sets:
            if self.filter_sets[filter_name]['cached']:
                if self.adapter.check_cached_item('%s/%s' % (filter_name, path)):
                    return redirect(
                        '%s/%s/%s' % (
                            self.adapter.source_folder,
                            self.adapter.cache_folder,
                            '%s/%s' % (filter_name, path)
                        )
                    )

            resource = self.adapter.get_item(path)

            if resource:
                for filter_item in self.filter_sets[filter_name]['filters']:
                    resource = filter_item.apply(resource)

                return redirect(self.adapter.create_cached_item('%s/%s' % (filter_name, path), resource))
            else:
                LOGGER.warning('File "%s" not found.' % path)
                abort(404)
        else:
            LOGGER.warning('Filter "%s" not found.' % filter_name)
            abort(404)


def imagine_filter(path, filter_name):  # pragma: no cover
    """
    Template filter
    :param path: image path
    :param filter_name: filter_name
    :param kwargs:
    :return:
    """
    self = current_app.extensions['imagine']
    return self.build_url(path, filter_name)
