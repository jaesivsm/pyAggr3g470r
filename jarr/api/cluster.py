from flask_jwt import current_identity, jwt_required
from flask_restx import Namespace, Resource, fields, inputs
from werkzeug.exceptions import Forbidden, NotFound

from jarr.api.common import parse_meaningful_params
from jarr.controllers import ClusterController
from jarr.lib.content_generator import migrate_content
from jarr.lib.enums import ReadReason
from jarr.metrics import READ

cluster_ns = Namespace('cluster', description='Cluster related operations')
cluster_parser = cluster_ns.parser()
cluster_parser.add_argument('liked', type=inputs.boolean,
                            nullable=False, store_missing=False)
cluster_parser.add_argument('read', type=inputs.boolean,
                            nullable=False, store_missing=False)
cluster_parser.add_argument('read_reason', type=str, required=False,
                            choices=[rr.value for rr in ReadReason],
                            nullable=False, store_missing=False)
article_model = cluster_ns.model('Article', {
    'id': fields.Integer(),
    'link': fields.String(),
    'feed_id': fields.Integer(),
    'title': fields.String(),
    'content': fields.String(required=True, default=''),
    'comments': fields.String(),
    'order_in_cluster': fields.Integer(default=0),
    'article_type': fields.String(attribute='article_type.value'),
    'date': fields.DateTime()})
content_model = cluster_ns.model('ProcessedContent', {
    'type': fields.String(required=True),
    'link': fields.String(required=True),
    'title': fields.String(skip_none=True),
    'content': fields.String(skip_none=True),
    'comments': fields.String(skip_none=True)})
model = cluster_ns.model('Cluster', {
    'id': fields.Integer(),
    'read': fields.Boolean(),
    'liked': fields.Boolean(),
    'main_feed_title': fields.String(),
    'main_article_id': fields.Integer(),
    'articles': fields.List(fields.Nested(article_model)),
    'contents': fields.List(fields.Nested(content_model, skip_none=True),
                            attribute=lambda c: c.content.get('contents')),
})


@cluster_ns.route('/<int:cluster_id>')
class ClusterResource(Resource):

    @staticmethod
    @cluster_ns.marshal_with(model, skip_none=True)
    @cluster_ns.response(200, 'OK')
    @cluster_ns.response(226, 'OK, marked as read')
    @cluster_ns.response(400, 'Validation error')
    @cluster_ns.response(401, 'Authorization needed')
    @cluster_ns.response(404, 'Not found')
    @jwt_required()
    def get(cluster_id):
        cctrl = ClusterController(cluster_identity.id)
        cluster = cctrl.get(id=cluster_id)
        code = 200
        cluster.content = migrate_content(cluster.content)
        if not cluster.read:
            cctrl.update({'id': cluster_id},
                         {'read': True, 'read_reason': ReadReason.read})
            READ.labels(reason=ReadReason.read.value).inc()
            cluster.read = True
            cluster.read_reason = ReadReason.read
            code = 226
        return cluster, code

    @staticmethod
    @cluster_ns.expect(cluster_parser)
    @cluster_ns.response(204, 'Updated')
    @cluster_ns.response(401, 'Authorization needed')
    @cluster_ns.response(403, 'Forbidden')
    @cluster_ns.response(404, 'Not found')
    @jwt_required()
    def put(cluster_id):
        cctrl = ClusterController(current_identity.id)
        attrs = parse_meaningful_params(cluster_parser)
        if 'read_reason' in attrs:
            pass  # not overriding given read reason
        elif 'read' in attrs and attrs.get('read'):
            attrs['read_reason'] = ReadReason.marked
            READ.labels(reason=ReadReason.marked.value).inc()
        elif 'read' in attrs and not attrs.get('read'):
            attrs['read_reason'] = None
        changed = cctrl.update({'id': cluster_id}, attrs)
        if not changed:
            cctrl.assert_right_ok(cluster_id)
        return None, 204

    @staticmethod
    @cluster_ns.response(204, 'Deleted')
    @cluster_ns.response(400, 'Validation error')
    @cluster_ns.response(401, 'Authorization needed')
    @cluster_ns.response(403, 'Forbidden')
    @cluster_ns.response(404, 'Not found')
    @jwt_required()
    def delete(cluster_id):
        try:
            ClusterController(current_identity.id).delete(cluster_id)
        except NotFound as not_found:
            user_id = ClusterController().get(id=cluster_id).user_id
            if user_id != current_identity.id:
                raise Forbidden() from not_found
            raise
        return None, 204
